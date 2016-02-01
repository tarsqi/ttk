"""

Simple Python Chunker

Usage

   from chunker import chunk_sentences
   chunked_sentences = chunk_sentences(sentences)
   
"""

from types import StringType


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
    #'TO', 'RB', 'RP', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ' ]

vp_final_tags = [
    'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ' ]

CHUNK_TAGS = { NG: { 'b': {}, 'i': {}, 'e': {} },
               VG: { 'b': {}, 'i': {}, 'e': {} } }

for tag in np_initial_tags: CHUNK_TAGS[NG]['b'][tag] = True
for tag in np_internal_tags: CHUNK_TAGS[NG]['i'][tag] = True
for tag in np_final_tags: CHUNK_TAGS[NG]['e'][tag] = True

for tag in vp_initial_tags: CHUNK_TAGS[VG]['b'][tag] = True
for tag in vp_internal_tags: CHUNK_TAGS[VG]['i'][tag] = True
for tag in vp_final_tags: CHUNK_TAGS[VG]['e'][tag] = True


# The following two are not used, but we could to make the chunker
# more precise.

NG_ORDER = [['DT','PRP$'], 
            ['CD', 'JJ','JJR','JJS','CC','VBG','VBN'],
            ['NN','NNS','NNP','NNPS']]
VG_ORDER = [['MD','RB','VB','VBD','VBG','VBN','VBZ'],
            ['VB','VBD','VBG','VBN', 'VBZ']]

# Accessing the CHUNK_TAGS dictionary

def is_initial_tag(cat, tag):
    """Returns True if tag can be cat-initial, False otherwise."""
    return CHUNK_TAGS[cat]['b'].get(tag,False)
    
def is_internal_tag(cat, tag):
    """Returns True if tag can be cat-internal, False otherwise."""
    return CHUNK_TAGS[cat]['i'].get(tag,False)
    
def is_final_tag(cat, tag):
    """Returns True if tag can be cat-final, False otherwise."""
    return CHUNK_TAGS[cat]['e'].get(tag,False)
    

# MAIN METHOD

def chunk_sentences(sentences):
    """Return a list of sentences with chunk tags added."""
    return [Sentence(s).chunk() for s in sentences]



# CLASSES

class Sentence:

    """The work horse for the chunker."""
    
    def __init__(self, sentence):
        """Set sentence variable and initialize chunk_tags dictionary."""
        self.sentence = sentence
        self.chunk_tags = { 'b': {}, 'e': {} }

    def chunk(self):
        """Chunk self.sentence. Updates the variable and returns it. Scans
        through the sentence, advancing the index if a chunk is found."""
        idx = 0
        while idx < len(self.sentence) - 1:
            tag = self.sentence[idx][1]
            # noun groups
            if is_initial_tag(NG, tag):
                new_idx = self.consume_chunk(NG, idx)
                if new_idx > idx:
                    idx = new_idx
                    continue
            # verb groups
            if is_initial_tag(VG, tag):
                new_idx = self.consume_chunk(VG, idx)
                if new_idx > idx:
                    idx = new_idx
                    continue
            # check for single pronouns, but only after we have tried noun groups
            if (tag == 'PRP' or tag == 'PP'):
                self.set_tags(NG, idx, idx)
                idx += 1
                continue
            idx += 1
        self.import_chunks()
        self.fix_common_errors()
        return self.sentence
    

    def consume_chunk(self, chunk_type, idx):
        """Read constituent of class chunk_type, starting at index
        idx. Returns idx if no constituent could be read, returns the
        index after the end of the consitutent otherwise."""

        # store first index of consitituent, set last index to a
        # negative value and get tag
        begin_idx = idx
        end_idx = -1
        tag = self.sentence[idx][1]

        # check whether current tag can end the constituent
        if is_final_tag(chunk_type, tag):
            end_idx = idx

        # skip first token (we already know it starts a constituent of
        # class chunk_type) and get new tag
        idx += 1
        tag = self.sentence[idx][1]
        
        # consume tags that can occur in the constituent, keeping
        # track of what the last potential ending tag was
        while is_internal_tag(chunk_type, tag):
            if is_final_tag(chunk_type, tag):
                end_idx = idx
            try:
                idx += 1
                tag = self.sentence[idx][1]
            except IndexError:
                # break out of the loop when hitting the end of the
                # sentence
                break
            
        if (end_idx > -1):
            # constituent found, set tags and return index after end
            self.set_tags(chunk_type, begin_idx, end_idx)
            return end_idx + 1
        else:
            # none found, return the initial index
            return begin_idx

        
    def set_tags(self, chunk_type, begin_idx, end_idx):
        """Store beginning and ending position of the hunk in the chunk_tags
        dictionary."""
        self.chunk_tags['b'][begin_idx] = chunk_type
        self.chunk_tags['e'][end_idx] = chunk_type

    def import_chunks(self):
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

        
    def fix_common_errors(self):
        """Phase 2 of processing. Fix some common errors."""

        self.fix_VBGs()

        # other candidates:
        #
        #   [DT NN DT NN] ==> [DT NN] [DT NN]
        #   (not needed any more, DT is never inside an NG)
        #
        #   [VBD VBD]==> [VBD] [VBD]
        #
        #   [DT NNP NNP CC DT NNP NNP NNP] ==> [DT NNP NN]P CC [DT NNP NNP NNP]
        #   eg: the World Bank and the International Monetary Fund
        #   (not needed anymore, a CC is never in an NG)
        

    def fix_VBGs(self):
        """The TreeTagger tends to tag some adjectives as gerunds, as a result
        we get
        
           [see/VBP sleeping/VBG] [men/NNS]

        This method finds these occurrences and moves the VBG in to the noun
        group:

           [see/VBP] [sleeping/VBG men/NNS]

        In order to do this, it finds all occurrences of VGs followed by NGs
        where: (i) the VG ends in VBG, (ii) the NG starts with one of NN, NNS,
        NNP, NNPS, and (iii) the verb before the VBG is not a form of "be".

        """

        for i in range(0,len(self.sentence)-5):
            if self.is_VB_VBG_NN(i):
                # move the VBG from position 2 to position 5
                token = self.sentence[i+1]
                del self.sentence[i+1:i+2]
                self.sentence.insert(i+3,token)

    def is_VB_VBG_NN(self, idx):
        """Return True if starting at idx, we have the pattern "NOT_BE VBG
        </VG> <NG> NN", return False otherwise."""

        def not_be(token):
            if len(token) > 2:
                return token[2] != 'be'
            else:
                return token[0] not in ('is', 'am', 'are')
            
        # TODO: this seems a bit brittle, but it does not appear to break
        return (not_be(self.sentence[idx])
                and self.sentence[idx][1] in ('VBP', 'VBZ', 'VBD', 'VB')
                and self.sentence[idx+1][1] == 'VBG'
                and self.sentence[idx+2] == '</vg>'
                and self.sentence[idx+3] == '<ng>'
                and self.sentence[idx+4][1] in ('NN', 'NNS', 'NNP', 'NNPS'))

    
    def pp(self):
        in_chunk = False
        for t in self.sentence:
            ss = '   '+str(t) if in_chunk else str(t)
            print ss
            if type(t) == StringType:
                in_chunk = not in_chunk


if __name__ == '__main__':

    # Example input with token, tag, stem, begin offset and end offset. The offsets are
    # not needed, but will be passed on in the output if they are given.
    s1 = [('Mr.', 'NNP', 'Mr.', 16, 19), ('Vinken', 'NNP', 'Vinken', 20, 26),
          ('got', 'VBD', 'get', 27, 30), ('the', 'DT', 'the', 31, 34),
          ('flue', 'NN', 'flue', 35, 39), ('on', 'IN', 'on', 40, 42),
          ('Nov.', 'NNP', 'Nov.', 43, 47), ('29th', 'JJ', '29th', 48, 52),
          ('.', '.', '.', 52, 53)]

    # Input with only token and tag is also excepted, but may result in a few more faulty
    # chunks
    s2 = [t[:2] for t in s1]
    
    for s in [s1, s2]:
        sentence = Sentence(s)
        sentence.chunk()
        sentence.pp()
