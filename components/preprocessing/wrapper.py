"""

Contains the wrappers for all preprocessing components.

"""

# There is some redundancy left between the PreprocessorWrapper on the one hand
# and the TokenizerWrapper, TaggerWrapper and ChunkerWrapper on the other. Much
# of it has been removed but in some cases changes on one end need to be
# accompanied by similar changes on the other. Would have liked to get rid of
# that by completely removing PreprocessorWrapper and defining the PREPROCESSOR
# pipeline element as a shorthand for TOKENIZER,TAGGER,CHUNKER. Unfortunately,
# it turns out that using the individual wrappers increases processing time by
# about 40% so we want to keep the PreprocessorWrapper around.


import os, sys, threading
from time import time
from subprocess import PIPE, Popen
from types import StringType, TupleType
from xml.sax.saxutils import escape, quoteattr

from utilities import logger
from docmodel.document import Tag
from library.tarsqi_constants import PREPROCESSOR, TOKENIZER, TAGGER, CHUNKER
from library.main import LIBRARY

from components.preprocessing.tokenizer import Tokenizer, TokenizedLex
from components.preprocessing.chunker import chunk_sentences


# TreeTagger executables and parameter file
MAC_EXECUTABLE = "tree-tagger"
LINUX_EXECUTABLE = "tree-tagger"
WINDOWS_EXECUTABLE = "tree-tagger.exe"
PARAMETER_FILE = "english-utf8.par"

# Markers for begin and end of text for TreeTagger. There is no potential
# conflict with substrings in the text that match these since the tokenizer will
# split off the brackets.
START_TEXT = "<start-text>"
END_TEXT = "<end-text>"

# Mappings for translating TreeTagger tags into tags expected by the chunker.
POS_MAPPINGS = { 'SENT': '.', 'NP': 'NNP', 'IN/that': 'IN' }


treetagger = None


class TagId():

    """Class to provide fresh identifiers for lex, ng, vg and s tags."""

    IDENTIFIERS = { 's': 0, 'c': 0, 'l': 0 }

    @classmethod
    def next(cls, prefix):
        cls.IDENTIFIERS[prefix] += 1
        return "%s%d" % (prefix, cls.IDENTIFIERS[prefix])

    @classmethod
    def reset(cls):
        cls.IDENTIFIERS = { 's': 0, 'c': 0, 'l': 0 }


def initialize_treetagger(treetagger_dir):
    global treetagger
    if treetagger is None:
        treetagger = TreeTagger(treetagger_dir)
    return treetagger


def normalize_POS(pos):
    """Some simple modifications of the TreeTagger POS tags."""
    if pos[0] == 'V' and pos[1] in ['V', 'H']:
        rest = pos[2:] if len(pos) > 2 else ''
        return 'VB' + rest
    else:
        return POS_MAPPINGS.get(pos, pos)


def adjust_lex_offsets(tokens, offset):
    """The tokenizer works on isolated strings, adding offsets relative to the
    beginning of the string. But for the lex tags we need to relate the offset
    to the beginning of the file, not to the beginning of some random
    string. This procedure is used to increment offsets on instances of
    TokenizedLex."""
    for token_string, token_object in tokens:
        # skip the ('<s>', None) pairs
        if token_object is not None:
            token_object.begin += offset
            token_object.end += offset


class Wrapper(object):

    """Abstract class for shared functionality of the proprocessing wrappers."""

    def __init__(self, name, tarsqidoc):
        self.component_name = name
        self.document = tarsqidoc
        self.terms = None

    def _init_tokenizer(self):
        self.tokenize_time = 0

    def _init_tagger(self):
        self.treetagger_dir = self.document.options.getopt('treetagger')
        self.treetagger = initialize_treetagger(self.treetagger_dir)
        self.tag_time = 0

    def _init_chunker(self):
        self.chunk_time = 0
        if self.document.options.import_events:
            self.terms = {}
            events = self.document.sourcedoc.tags.find_tags(LIBRARY.timeml.EVENT)
            for event in events:
                self.terms[event.begin] = event

    def _tokenize_text(self, string):
        """Takes a unicode string and returns a list of objects, where each
        object is either the pair ('<s>', None) or a pair of a tokenized string
        and a TokenizedLex instance."""
        t1 = time()
        tokenizer = Tokenizer(string)
        tokenized_text = tokenizer.tokenize_text()
        pairs = tokenized_text.as_pairs()
        self.tokenize_time += time() - t1
        return pairs

    def _tag_text(self, tokens):
        """Takes a string and returns a list of sentences. Each sentence is a
        list of tuples of token, part-of-speech and lemma."""
        t1 = time()
        vertical_string = "\n".join([t[0] for t in tokens])
        # this avoids handler warning if input is empty
        if not vertical_string.strip():
            vertical_string = '<s>'
        # treetagger does not accept a unicode string, so encode in utf-8
        # TODO: this may have changed with the latest version
        taggedItems = self.treetagger.tag_text(vertical_string.encode('utf-8'))
        # The taggedItems result is the same whether you run this from the
        # PreprocessorWrapper or the TaggerWrapper, but those two use slightly
        # different _merge_tags() methods so the result is different
        text = self._merge_tags(tokens, taggedItems)
        self.tag_time += time() - t1
        return text

    def _chunk_text(self, text):
        """Takes a list of sentences and return the same sentences with chunk
        tags inserted."""
        # TODO: May need to do deal with things like &, <, >, and others
        t1 = time()
        chunked_text = chunk_sentences(text, self.terms)
        self.chunk_time += time() - t1
        return chunked_text


class PreprocessorWrapper(Wrapper):

    """Wrapper for the preprocessing components."""

    def __init__(self, tarsqidocument):
        """Set component_name, add the TarsqiDocument and initialize the
        TreeTagger."""
        Wrapper.__init__(self, PREPROCESSOR, tarsqidocument)
        self._init_tokenizer()
        self._init_tagger()
        self._init_chunker()

    def process(self):
        """Retrieve the element tags from the TarsqiDocument and hand the text
        for the elements as strings to the preprocessing chain. The result is a
        shallow tree with sentences and tokens. These are inserted into the
        TarsqiDocument's tags TagRepositories."""
        TagId.reset()
        for element in self.document.elements():
            text = self.document.sourcedoc.text[element.begin:element.end]
            tokens = self._tokenize_text(text)
            adjust_lex_offsets(tokens, element.begin)
            text = self._tag_text(tokens)
            # TODO: add some code to get lemmas when the TreeTagger just gets
            # <unknown>, see https://github.com/tarsqi/ttk/issues/5
            text = self._chunk_text(text)
            self._export(text)
        logger.info("tokenizer processing time: %.3f seconds" % self.tokenize_time)
        logger.info("tagger processing time: %.3f seconds" % self.tag_time)
        logger.info("chunker processing time: %.3f seconds" % self.chunk_time)

    def _merge_tags(self, tokens, taggedItems):
        text = []
        current_sentence = []
        for (token, item) in zip(tokens, taggedItems):
            if item == '<s>':
                current_sentence = []
                text.append(current_sentence)
                continue
            lex = token[1]
            if item[0] == '<' and item[-1] == '>':
                # not quite sure what these are for, probably tags that the
                # TreeTagger leaves alone
                token_tuple = (item[0], 'SYM', item[0], lex.begin, lex.end)
                current_sentence.append(token_tuple)
            else:
                (tok, pos, stem) = item.split("\t")
                pos = normalize_POS(pos)
                current_sentence.append((tok, pos, stem, lex.begin, lex.end))
        return text

    def _export(self, text):
        """Export preprocessing information to the tag repository. Updates the
        TagRepository using the preprocessing result."""
        ctag = None
        for sentence in text:
            sentence_attrs = { 'id': TagId.next('s'), 'origin': PREPROCESSOR }
            stag = Tag('s', None, None, sentence_attrs)
            for token in sentence:
                if self._is_tag(token):
                    if not token.startswith('</'):
                        ctag = Tag(token[1:-1], None, None,
                                   { 'id': TagId.next('c'), 'origin': PREPROCESSOR })
                    else:
                        ctag.end = last_ltag.end
                        self.document.tags.append(ctag)
                        ctag = None
                elif type(token) == TupleType:
                    ltag = self._make_ltag(token)
                    self.document.tags.append(ltag)
                    if stag.begin is None:
                        stag.begin = token[3]
                    if ctag is not None and ctag.begin is None:
                        ctag.begin = ltag.begin
                    last_end_offset = token[4]
                    last_ltag = ltag
                else:
                    logger.warn('Unexpected token type')
            stag.end = last_ltag.end
            self.document.tags.append(stag)
            # this indexing is needed because we bypassed the add_tag method on
            # TagRepository and instead directly appended to the tags list
            self.document.tags.index()

    @staticmethod
    def _is_tag(token):
        """Return True if token is a string starting with < and ending with >."""
        return type(token) == StringType \
            and token.startswith('<') \
            and token.endswith('>')

    @staticmethod
    def _make_ltag(token):
        """Return an instance of Tag for the token."""
        return Tag('lex', token[3], token[4],
                   { 'id': TagId.next('l'), 'lemma': token[2], 'pos': token[1],
                     'text': token[0], 'origin': PREPROCESSOR })


class TokenizerWrapper(Wrapper):

    """Wrapper for the tokenizer."""

    def __init__(self, tarsqidocument):
        """Set component_name and add the TarsqiDocument."""
        Wrapper.__init__(self, TOKENIZER, tarsqidocument)
        self._init_tokenizer()

    def process(self):
        """Retrieve the element tags from the TarsqiDocument and hand the text for
        the elements as strings to the tokenizer. The result is a list of pairs,
        where the pair is either (<s>, None) or (SomeString, TokenizedLex). In
        the first case an s tag is inserted in the TarsqiDocument's tags
        TagRepository and in the second a lex tag."""
        TagId.reset()
        for element in self.document.elements():
            text = self.document.sourcedoc.text[element.begin:element.end]
            tokens = self._tokenize_text(text)
            adjust_lex_offsets(tokens, element.begin)
            self._export_tokens(tokens)

    def _export_tokens(self, tokens):
        """Add s tags and lex tags to the TagRepository of the TarsqiDocument."""
        tokens = self._filter_tokens(tokens)
        s_begin, s_end = None, None
        for t in tokens:
            if t == '<s>':
                self._export_sentence(s_begin, s_end)
                s_begin, s_end = None, None
            else:
                begin, end = t.begin, t.end
                lid = TagId.next('l')
                ltag = Tag('lex', begin, end,
                           { 'id': lid, 'text': t.text, 'origin': TOKENIZER })
                self.document.tags.append(ltag)
                if s_begin is None:
                    s_begin = begin
                s_end = end
        self._export_sentence(s_begin, s_end)
        self.document.tags.index()

    def _export_sentence(self, s_begin, s_end):
        """Add an s tag to the TagRepository of the TarsqiDocument."""
        if s_begin is not None:
            stag = Tag('s', s_begin, s_end,
                       { 'id': TagId.next('s'), 'origin': TOKENIZER })
            self.document.tags.append(stag)

    @staticmethod
    def _filter_tokens(tokens):
        """The tokens list is a list of pairs, where the first element is '<s>'
        or the text of the token and the second element either None if the first
        element is '<s>' or a TokenizedLex instance, just keep the '<s>' or the
        TokenizedLex."""
        filtered_tokens = []
        for t in tokens:
            core = t[0] if t[0] == '<s>' else t[1]
            filtered_tokens.append(core)
        return filtered_tokens


class TaggerWrapper(Wrapper):

    """Wrapper for the tagger."""

    def __init__(self, tarsqidocument):
        """Set component_name, add the TarsqiDocument and initialize the
        TreeTagger."""
        Wrapper.__init__(self, TAGGER, tarsqidocument)
        self._init_tagger()

    def process(self):
        """Generate input for the tagger from the lex and s tags in the document, run
        the tagger, and insert the new information (pos and lemma) into the
        TagRepository on the TarsqiDocument."""
        for element in self.document.elements():
            sentences = self.document.tags.find_tags('s', element.begin, element.end)
            lexes = self.document.tags.find_tags('lex', element.begin, element.end)
            tokens = []
            for s in sentences:
                tokens.append(('<s>', None))
                lexes_in_s = [l for l in lexes if l.begin >= s.begin and l.end <= s.end]
                for l in sorted(lexes_in_s):
                    text = l.attrs['text']
                    tokens.append((text, TokenizedLex(l.begin, l.end, text)))
            tagged_tokens = self._tag_text(tokens)
            # TODO: add some code to get lemmas when the TreeTagger just gets
            # <unknown>, see https://github.com/tarsqi/ttk/issues/5
            self._export_tags(tagged_tokens)

    def _merge_tags(self, tokens, taggedItems):
        """Merge the tags and lemmas into the tokens. Result is a list of tokens
        where each token is a 5-tuple of text, tag, lemma, begin offset and end
        offset. Sentence information is not kept in this list, which makes this
        method different from it's sister on PreprocessorWrapper."""
        # TODO: see if thismethod can me merged with the other _merge_tags() method
        text = []
        for (token, item) in zip(tokens, taggedItems):
            if item == '<s>':
                continue
            lex = token[1]
            if item[0] == '<' and item[-1] == '>':
                # not quite sure what these are for, probably tags that the
                # TreeTagger leaves alone
                token_tuple = (item[0], 'SYM', item[0], lex.begin, lex.end)
                text.append(token_tuple)
            else:
                (tok, pos, stem) = item.split("\t")
                pos = normalize_POS(pos)
                text.append((tok, pos, stem, lex.begin, lex.end))
        return text

    def _export_tags(self, tagged_tokens):
        """Take the token tuples and add their pos and lemma information to the
        TagRepository in the TarsqiDocument."""
        for tagged_token in tagged_tokens:
            pos, lemma, p1, p2 = tagged_token[1:5]
            tags = self.document.tags.find_tags_at(p1)
            tags = [t for t in tags if t.end == p2 and t.name == 'lex']
            if len(tags) == 1:
                tags[0].attrs['pos'] = pos
                tags[0].attrs['lemma'] = lemma
                tags[0].attrs['origin'] += ",%s" % TAGGER
            else:
                logger.warn("More than one lex tag at position %d-%d" % (p1, p2))


class ChunkerWrapper(Wrapper):

    """Wrapper for the chunker."""

    def __init__(self, tarsqidocument):
        """Set component_name, add the TarsqiDocument and initialize the chunker."""
        Wrapper.__init__(self, CHUNKER, tarsqidocument)
        self._init_chunker()

    def process(self):
        """Generate input for the chunker from the lex and s tags in the document,
        run the chunker, and insert the new ng and vg chunks into the TagRepository
        on the TarsqiDocument."""
        TagId.reset()
        for element in self.document.elements():
            text = self._import_tokens(element)
            text = self._chunk_text(text)
            self._export_chunks(text)

    def _import_tokens(self, element):
        """Import sentence and lex tags and create the datastructure that the chunker
        needs as input."""
        sentences = self.document.tags.find_tags('s', element.begin, element.end)
        lexes = self.document.tags.find_tags('lex', element.begin, element.end)
        text = []
        for s in sentences:
            sentence = []
            lexes_in_s = [l for l in lexes if l.begin >= s.begin and l.end <= s.end]
            for l in sorted(lexes_in_s):
                token = (l.attrs['text'], l.attrs['pos'], l.attrs['lemma'], l.begin, l.end)
                sentence.append(token)
            text.append(sentence)
        return text

    def _export_chunks(self, text):
        """Export ng and vg tags to the TagRepository on the TarsqiDocument."""
        for sentence in text:
            in_chunk = False
            chunk_begin = None
            chunk_end = None
            for token in sentence:
                if token in ('<ng>', '<vg>'):
                    in_chunk = True
                    chunk_begin = None
                    chunk_end = None
                elif token in ('</ng>', '</vg>'):
                    in_chunk = False
                    chunk_tag = token[2:-1]
                    ctag = Tag(chunk_tag, chunk_begin, chunk_end,
                               { 'id': TagId.next('c'), 'origin': CHUNKER })
                    self.document.tags.append(ctag)
                elif in_chunk:
                    if chunk_begin is None:
                        chunk_begin = token[3]
                    chunk_end = token[4]
        self.document.tags.index()


class TreeTagger(object):

    """Class that wraps the TreeTagger."""

    def __init__(self, treetagger_dir):
        """Set up the pipe to the TreeTagger."""
        self.dir = os.path.abspath(treetagger_dir)
        self.bindir = os.path.join(self.dir, "bin")
        self.libdir = os.path.join(self.dir, "lib")
        executable = self._get_executable()
        parfile = os.path.join(self.libdir, PARAMETER_FILE)
        tagcmd = "%s -token -lemma -sgml %s" % (executable, parfile)
        # when using subprocess, need to use a different close_fds for windows
        close_fds = False if sys.platform == 'win32' else True
        self.process = Popen(tagcmd, shell=True,
                             stdin=PIPE, stdout=PIPE, close_fds=close_fds)

    def _get_executable(self):
        """Get the TreeTagger executable for the platform."""
        if sys.platform == "win32":
            executable = os.path.join(self.bindir, WINDOWS_EXECUTABLE)
        elif sys.platform == "linux2":
            executable = os.path.join(self.bindir, LINUX_EXECUTABLE)
        elif sys.platform == "darwin":
            executable = os.path.join(self.bindir, MAC_EXECUTABLE)
        else:
            logger.error("No binary for platform %s" % sys.platform)
        if not os.path.isfile(executable):
            logger.error("TreeTagger binary invalid: %s" % executable)
        return executable

    def __del__(self):
        """When deleting the wrapper, close the TreeTagger process pipes."""
        self.process.stdin.close()
        self.process.stdout.close()

    def tag_text(self, text):
        """Open a thread to the TreeTagger, pipe in the text and return the results."""
        # We add a period as an extra token. This is a hack to deal with a nasty
        # problem where sometimes the TreeTagger will not return a value. It is
        # not clear why this is. Later in this method we pop off the extra tag
        # that we get because of this. TODO: it would be better to deal with
        # this in a more general way, see multiprocessing.Pool with a timeout.
        text += "\n.\n"
        args = (self.process.stdin, text)
        thread = threading.Thread(target=_write_to_stdin, args=args)
        thread.start()
        result = []
        collect = False
        while True:
            line = self.process.stdout.readline().strip()
            if line == START_TEXT:
                collect = True
            elif line == END_TEXT:
                break
            elif line and collect:
                result.append(line)
        thread.join()
        result.pop()
        return result


def _write_to_stdin(pipe, text):
    pipe.write("%s\n" % START_TEXT)
    if text:
        pipe.write("%s\n" % text)
        # NOTE. Without the following the tagger will hang. Do not try to make
        # it shorter, it may need at least a space, but I have no idea why.
        pipe.write("%s\n.\ndummy sentence\n.\n" % END_TEXT)
        pipe.flush()
