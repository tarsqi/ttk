"""Simple Python Chunker

Usage

   from chunker import chunk_sentences
   chunked_sentences = chunk_sentences(sentences)
   chunked_sentences = chunk_sentences(sentences, terms)

The optional terms argument allows you to hand in a dictionary of terms indexed
on their beginning offsets. With this dictionary, terms are always considered
chunks as long as they are headed by a noun or verb. Terms are instances of
docmodel.document.Tag.

"""

# TODO
#
# For the chunks derived from terms We might want to consider adding all terms
# from all offsets and then merging them afterwards. So if we have an NG chunk
# from 1-3 and there is a term from 2-4, then we add 1-4 (now we only add
# 1-3). This would be a more global change that is not restricted to the
# _consume_term() method.
#
# For more details see https://github.com/tarsqi/ttk/issues/63.


from types import StringType

from utilities import logger
from components.common_modules.tree import create_tarsqi_tree

from library.tarsqi_constants import GUTIME


# CHUNK TYPES

NG = 'ng'
VG = 'vg'


# TAG DICTIONARY

# Definition of what tags can start a chunk, be inside a chunk and end
# a chunk
#
# Removed CC from np_internal_tags. Will incorrectly chunk "JJ CC JJ
# NN". May want to add it back in and deal with [NN and NN] by
# splitting it.  Also removed DT, so "DT NN DT NN" is not one chunk,
# we could now miss things like "DT DT NN" (if they exist).

np_initial_tags = [
    'DT', 'PRP$', 'CD', 'JJ', 'JJR', 'JJS', 'NN', 'NNS', 'NNP',
    'NNPS', 'VBG', 'VBN' ]

np_internal_tags = [
    'PRP$', 'EX', 'CD', 'JJ', 'JJR', 'JJS', 'NN', 'NNP', 'NNPS',
    'NNS', 'VBG', 'VBN' ]

np_final_tags = [
    'NN', 'NNS', 'NNP', 'NNPS' ]

vp_initial_tags = [
    'TO', 'MD', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ' ]

vp_internal_tags = [
    'RB', 'RP', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ' ]
    # 'TO', 'RB', 'RP', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ' ]

vp_final_tags = [
    'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ' ]

CHUNK_TAGS = {
    NG: { 'b': { t:True for t in np_initial_tags },
          'i': { t:True for t in np_internal_tags },
          'e': { t:True for t in np_final_tags } },
    VG: { 'b': { t:True for t in vp_initial_tags },
          'i': { t:True for t in vp_internal_tags },
          'e': { t:True for t in vp_final_tags } } }


# The following two are not used, but we could to make the chunker
# more precise.

NG_ORDER = [['DT', 'PRP$'],
            ['CD', 'JJ', 'JJR', 'JJS', 'CC', 'VBG', 'VBN'],
            ['NN', 'NNS', 'NNP', 'NNPS']]
VG_ORDER = [['MD', 'RB', 'VB', 'VBD', 'VBG', 'VBN', 'VBZ'],
            ['VB', 'VBD', 'VBG', 'VBN', 'VBZ']]


# MAIN METHOD

def chunk_sentences(sentences, terms=None):
    """Return a list of sentences with chunk tags added."""
    return [Sentence(s).chunk(terms) for s in sentences]


# CLASSES

class Sentence:

    """The work horse for the chunker."""

    def __init__(self, sentence):
        """Set sentence variable and initialize chunk_tags dictionary."""
        self.sentence = sentence
        self.chunk_tags = {'b': {}, 'e': {}}

    def chunk(self, terms=None):
        """Chunk self.sentence. Updates the variable and returns it. Scans
        through the sentence and advances the index if a chunk is found. The
        optional terms argument contains a dictionary of terms indexed on start
        offset. If a terms dictionary is handed in then use it to make sure that
        terms on it are considered chunks (as long as they are headed by a noun
        or verb)."""
        idx = 0
        while idx < len(self.sentence) - 1:
            tag = self.sentence[idx][1]
            tag_begin = self.sentence[idx][3]
            # terms
            if _is_term_initial_offset(tag_begin, terms):
                term = terms[tag_begin]
                new_idx = self._consume_term(term, idx)
                if new_idx > idx:
                    idx = new_idx
                    continue
            # noun groups
            if _is_initial_tag(NG, tag):
                new_idx = self._consume_chunk(NG, idx)
                if new_idx > idx:
                    idx = new_idx
                    continue
            # verb groups
            if _is_initial_tag(VG, tag):
                new_idx = self._consume_chunk(VG, idx)
                if new_idx > idx:
                    idx = new_idx
                    continue
            # check for single pronouns, but only after we have tried noun groups
            if (tag == 'PRP' or tag == 'PP'):
                self._set_tags(NG, idx, idx)
                idx += 1
                continue
            idx += 1
        self._import_chunks()
        self._fix_common_errors()
        return self.sentence


    def _consume_term(self, term, idx):
        """Now that we now that a term starts at index idx, read the whole term
        and, if it matches a few requirements, add it to the chunk_tags
        dictionary. A term is an instance of docmodel.document.Tag."""
        begin_idx = idx
        end_idx = -1
        tag = self.sentence[idx]
        while term.begin <= tag[3] < term.end:
            end_idx = idx
            idx += 1
            if idx >= len(self.sentence):
                break
            tag = self.sentence[idx]
        final_tag = self.sentence[idx-1]
        if (end_idx > -1) and (final_tag[4] == term.end):
            # constituent found, set tags and return index after end
            pos = final_tag[1]
            if pos.startswith('V'):
                chunk_type = VG
            elif pos.startswith('N'):
                chunk_type = NG
            else:
                # do not create a chunk if this was not headed by a noun or verb
                return begin_idx
            self._set_tags(chunk_type, begin_idx, end_idx)
            return end_idx + 1
        else:
            # none found, return the initial index, this should actually not
            # happen so log a warning
            logger.warn("Could not consume full term")
            return begin_idx


    def _consume_chunk(self, chunk_type, idx):
        """Read constituent of class chunk_type, starting at index idx. Returns
        idx if no constituent could be read, returns the index after the end of the
        consitutent otherwise."""

        # store first index of consitituent, set last index to a negative value
        # and get tag
        begin_idx = idx
        end_idx = -1
        tag = self.sentence[idx][1]

        # check whether current tag can end the constituent
        if _is_final_tag(chunk_type, tag):
            end_idx = idx

        # skip first token (we already know it starts a constituent of class
        # chunk_type) and get new tag
        idx += 1
        tag = self.sentence[idx][1]

        # consume tags that can occur in the constituent, keeping track of what
        # the last potential ending tag was
        while _is_internal_tag(chunk_type, tag):
            if _is_final_tag(chunk_type, tag):
                end_idx = idx
            try:
                idx += 1
                tag = self.sentence[idx][1]
            except IndexError:
                # break out of the loop when hitting the end of the sentence
                break

        if (end_idx > -1):
            # constituent found, set tags and return index after end
            self._set_tags(chunk_type, begin_idx, end_idx)
            return end_idx + 1
        else:
            # none found, return the initial index
            return begin_idx


    def _set_tags(self, chunk_type, begin_idx, end_idx):
        """Store beginning and ending position of the hunk in the chunk_tags
        dictionary."""
        self.chunk_tags['b'][begin_idx] = chunk_type
        self.chunk_tags['e'][end_idx] = chunk_type

    def _import_chunks(self):
        """Add chunk tags to the sentence variable."""
        new_sentence = []
        idx = 0
        for token in self.sentence:
            chunk = self.chunk_tags['b'].get(idx, None)
            if chunk:
                new_sentence.append('<'+chunk+'>')
            new_sentence.append(token)
            chunk = self.chunk_tags['e'].get(idx, None)
            if chunk:
                new_sentence.append('</'+chunk+'>')
            idx += 1
        self.sentence = new_sentence


    def _fix_common_errors(self):
        """Phase 2 of processing. Fix some common errors."""

        self._fix_VBGs()

        # other candidates:
        #
        #   [JJ NN VBG NNS] ==> [JJ NN] [VBG NNS]
        #   eg: early pneumonia pending cultures
        #   this would also be fixed when using NG_ORDER
        #
        #   [DT NN DT NN] ==> [DT NN] [DT NN]
        #   (not needed any more, DT is never inside an NG)
        #
        #   [VBD VBD]==> [VBD] [VBD]
        #
        #   [DT NNP NNP CC DT NNP NNP NNP] ==> [DT NNP NN]P CC [DT NNP NNP NNP]
        #   eg: the World Bank and the International Monetary Fund
        #   (not needed anymore, a CC is never in an NG)


    def _fix_VBGs(self):
        """The TreeTagger tends to tag some adjectives as gerunds, as a result
        we get

           [see/VBP sleeping/VBG] [men/NNS]

        This method finds these occurrences and moves the VBG in to the noun
        group:

           [see/VBP] [sleeping/VBG men/NNS]

        In order to do this, it finds all occurrences of VGs followed by NGs
        where: (i) the VG ends in VBG, (ii) the NG starts with one of NN, NNS,
        NNP, NNPS, and (iii) the verb before the VBG is not a form of "be"."""

        for i in range(0, len(self.sentence)-5):
            if self._is_VB_VBG_NN(i):
                # move the VBG from position 2 to position 5
                token = self.sentence[i+1]
                del self.sentence[i+1:i+2]
                self.sentence.insert(i+3, token)

    def _is_VB_VBG_NN(self, idx):
        """Return True if starting at idx, we have the pattern "NOT_BE VBG
        </VG> <NG> NN", return False otherwise."""
        def not_be(token):
            if len(token) > 2:
                return token[2] != 'be'
            else:
                return token[0] not in ('is', 'am', 'are')
        try:
            # this should not throw errors due to the test done before calling
            # this method, but check anyway
            return (not_be(self.sentence[idx])
                    and self.sentence[idx][1] in ('VBP', 'VBZ', 'VBD', 'VB')
                    and self.sentence[idx+1][1] == 'VBG'
                    and self.sentence[idx+2] == '</vg>'
                    and self.sentence[idx+3] == '<ng>'
                    and self.sentence[idx+4][1] in ('NN', 'NNS', 'NNP', 'NNPS'))
        except IndexError:
            logger.warn("Unexpected index error")
            return False

    def pp_tokens(self):
        for e in self.sentence:
            if type(e) == type((None,)):
                print e[0],
        print

    def pp(self):
        in_chunk = False
        for t in self.sentence:
            ss = '   '+str(t) if in_chunk else str(t)
            print ss
            if type(t) == StringType:
                in_chunk = not in_chunk


# Accessing the CHUNK_TAGS dictionary

def _is_initial_tag(cat, tag):
    """Returns True if tag can be cat-initial, False otherwise."""
    return CHUNK_TAGS[cat]['b'].get(tag, False)

def _is_internal_tag(cat, tag):
    """Returns True if tag can be cat-internal, False otherwise."""
    return CHUNK_TAGS[cat]['i'].get(tag, False)

def _is_final_tag(cat, tag):
    """Returns True if tag can be cat-final, False otherwise."""
    return CHUNK_TAGS[cat]['e'].get(tag, False)

def _is_term_initial_offset(begin, terms):
    """Returns True if begin is a key in terms."""
    return terms is not None and begin in terms


class ChunkUpdater(object):

    """Class that allows you to take a TarsqiDocument and then update the chunks
    in it given tags that were unsuccesfully added to the TarsqiTrees in the
    document. Currently only done for Timex tags."""

    def __init__(self, tarsqidoc):
        self.tarsqidoc = tarsqidoc

    @staticmethod
    def _get_containing_sentence(doctree, orphan):
        """Returns the sentence that contains the orphan tag, or None if no such
        unique sentence exists."""
        sentences = [s for s in doctree.dtrs if s.includes(orphan)]
        return sentences[0] if len(sentences) == 1 else None

    def update(self):
        """Uses the orphans in the TarsqiTrees in the document to update chunks."""
        for element in self.tarsqidoc.elements():
            self._update_element(element)

    def _update_element(self, element):
        """Uses the orphans in the TarsqiTree of the element to update chunks."""
        # NOTE: this is generic sounding, but is really only meant for timexes
        # TODO: maybe rename while the above is the case
        doctree = create_tarsqi_tree(self.tarsqidoc, element)
        for orphan in doctree.orphans:
            sentence = self._get_containing_sentence(doctree, orphan)
            if sentence is None:
                logger.warn("No sentence contains %s" % orphan)
                continue
            nodes = [n for n in sentence.all_nodes() if n.overlaps(orphan)]
            nodes = [n for n in nodes if n is not sentence and not n.isToken()]
            #self._debug(orphan, sentence, nodes)
            self._remove_overlapping_chunks(nodes)
        self._add_chunks_for_timexes(element)

    def _remove_overlapping_chunks(self, nodes):
        """Remove all the noun chunk nodes that were found to be overlapping."""
        for node in nodes:
            if node.isChunk():
                self.tarsqidoc.tags.remove_tag(node.tag)

    def _add_chunks_for_timexes(self, element):
        # At this point we have removed chunks that overlap with timexes. The
        # TarsqiTree used in the calling method did not know that (because
        # changes were made to the TagRepository. So we create a new tree.
        doctree = create_tarsqi_tree(self.tarsqidoc, element)
        # Note that it is perhaps not enough to just create a chunk for the
        # orphan because removing an overlapping chunk could remove a chunk that
        # also embed another timex, which will then have no chunk around it. A
        # more primary question by the way is, do we need timexes to be inside
        # chunks or can they stand by themselves for later processing?
        # TODO: check whether we can go without chunks or whether we need
        # timexes to be inside chunks.
        for sentence in doctree.get_sentences():
            nodes = sentence.all_nodes()
            timexes = [n for n in nodes if n.isTimex()]
            nounchunks = [n for n in nodes if n.isNounChunk()]
            for t in timexes:
                # if the timexes parent is a sentence, then add a Tag with
                # tagname ng to the TagRepository
                if t.parent.isSentence():
                    # for now we will credit GUTIME with this chunk
                    attrs = { 'origin':  GUTIME }
                    self.tarsqidoc.tags.add_tag(NG, t.begin, t.end, attrs)

    @staticmethod
    def _debug(orphan, sentence, nodes):
        if True:
            print orphan
            print '  ', sentence
            for n in nodes:
                print '  ', n
                print '  ', n.tag



if __name__ == '__main__':

    # NOTE: if you want to run this as a standalone script then you should
    # comment out the logger import

    # Example input with token, tag, stem, begin offset and end offset.
    s1 = [('Mr.', 'NNP', 'Mr.', 16, 19), ('Vinken', 'NNP', 'Vinken', 20, 26),
          ('got', 'VBD', 'get', 27, 30), ('the', 'DT', 'the', 31, 34),
          ('flue', 'NN', 'flue', 35, 39), ('on', 'IN', 'on', 40, 42),
          ('Nov.', 'NNP', 'Nov.', 43, 47), ('29th', 'JJ', '29th', 48, 52),
          ('.', '.', '.', 52, 53)]

    for s in [s1]:
        sentence = Sentence(s)
        sentence.chunk()
        sentence.pp()
