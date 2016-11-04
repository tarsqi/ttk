"""

Contains the wrapper for all preprocessing components.

"""

import os, sys, threading
from time import time
from subprocess import PIPE, Popen
from types import StringType, TupleType
from xml.sax.saxutils import escape, quoteattr

from utilities import logger
from docmodel.document import Tag
from library.tarsqi_constants import PREPROCESSOR

from components.preprocessing.tokenizer import Tokenizer
from components.preprocessing.chunker import chunk_sentences

# TreeTagger executables and parameter file
MAC_EXECUTABLE = "tree-tagger"
LINUX_EXECUTABLE = "tree-tagger"
WINDOWS_EXECUTABLE = "tree-tagger.exe"
PARAMETER_FILE = "english-utf8.par"

# Markers for begin and end of text for TreeTagger. There is no potential
# conflict with substrangs in the text that mtch these since the tokenizer will
# split off the brackets.
START_TEXT = "<start-text>"
END_TEXT = "<end-text>"

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


def normalizePOS(pos):
    """Some simple modifications of the TreeTagger POS tags."""
    if pos == 'SENT':
        pos = '.'
    elif pos[0] == 'V':
        if pos[1] in ['V', 'H']:
            if len(pos) > 2:
                rest = pos[2:]
            else:
                rest = ''
            pos = 'VB' + rest
    elif pos == "NP":
        pos = "NNP"
    # new version of treetagger changed the tag for 'that'
    elif pos == 'IN/that':
        pos = 'IN'
    return pos


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


class PreprocessorWrapper:

    """Wrapper for the preprocessing components."""

    def __init__(self, tarsqidocument):
        """Set component_name, add the TarsqiDocument and initialize the
        TreeTagger."""
        self.component_name = PREPROCESSOR
        self.document = tarsqidocument
        self.treetagger_dir = self.document.options.getopt('treetagger')
        self.treetagger = initialize_treetagger(self.treetagger_dir)
        self.tokenize_time = 0
        self.tag_time = 0
        self.chunk_time = 0

    def process(self):
        """Retrieve the element tags from the TarsqiDocument and hand the text
        for the elements as strings to the preprocessing chain. The result is a
        shallow tree with sentences and tokens. These are inserted into the
        TarsqiDocument's tags TagRepositories. """
        TagId.reset()
        for element in self.document.elements():
            text = self.document.sourcedoc.text[element.begin:element.end]
            tokens = self.tokenize_text(text)
            adjust_lex_offsets(tokens, element.begin)
            text = self.tag_text(tokens)
            # TODO: add some code to get lemmas when the TreeTagger just gets
            # <unknown>, see https://github.com/tarsqi/ttk/issues/5
            text = self.chunk_text(text)
            export(text, self.document)
        logger.info("tokenizer processing time: %.3f seconds" % self.tokenize_time)
        logger.info("tagger processing time: %.3f seconds" % self.tag_time)
        logger.info("chunker processing time: %.3f seconds" % self.chunk_time)

    def tokenize_text(self, string):
        """Takes a unicode string and returns a list of objects, where each
        object is either the pair ('<s>', None) or a pair of a tokenized string
        and a TokenizedLex instance."""
        t1 = time()
        tokenizer = Tokenizer(string)
        tokenized_text = tokenizer.tokenize_text()
        pairs = tokenized_text.as_pairs()
        self.tokenize_time += time() - t1
        return pairs

    def tag_text(self, tokens):
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
        text = self.create_text_from_tokens_and_tags(tokens, taggedItems)
        self.tag_time += time() - t1
        return text

    def chunk_text(self, text):
        """Takes a list of sentences and return the same sentences with chunk
        tags inserted. May need to do something with things like &, <, >, and
        others."""
        t1 = time()
        chunked_text = chunk_sentences(text)
        self.chunk_time += time() - t1
        return chunked_text

    def create_text_from_tokens_and_tags(self, tokens, taggedItems):
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
                pos = normalizePOS(pos)
                current_sentence.append((tok, pos, stem, lex.begin, lex.end))
        return text


def export(text, tarsqidoc):
    """Export preprocessing information to the tag repository. Updates the
    TagRepository using the preprocessing result."""
    ctag = None
    for sentence in text:
        stag = Tag(TagId.next('s'), 's', None, None, {'origin': PREPROCESSOR})
        for token in sentence:
            if _is_tag(token):
                if not token.startswith('</'):
                    ctag = Tag(TagId.next('c'), token[1:-1], None, None,
                               {'origin': PREPROCESSOR})
                else:
                    ctag.end = last_ltag.end
                    tarsqidoc.tags.append(ctag)
                    ctag = None
            elif type(token) == TupleType:
                ltag = _make_ltag(token)
                tarsqidoc.tags.append(ltag)
                if stag.begin is None:
                    stag.begin = token[3]
                if ctag is not None and ctag.begin is None:
                    ctag.begin = ltag.begin
                last_end_offset = token[4]
                last_ltag = ltag
            else:
                logger.warn('Unexpected token type')
        stag.end = last_ltag.end
        tarsqidoc.tags.append(stag)
    # this indexing is needed because we bypassed the add_tag method on
    # TagRepository and instead directly appended to the tags list
    tarsqidoc.tags.index()


def _is_tag(token):
    return type(token) == StringType \
        and token.startswith('<') \
        and token.endswith('>')


def _make_ltag(token):
    """Return an instance of Tag for the token."""
    return Tag(TagId.next('l'), 'lex', token[3], token[4],
               { 'lemma': token[2], 'pos': token[1], 'text': token[0],
                 'origin': PREPROCESSOR })


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
        """Open a thread to the TreeTagger and get results."""
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
        thread.join()  # this may avoid problems
        return result


def _write_to_stdin(pipe, text):
    pipe.write("%s\n" % START_TEXT)
    if text:
        pipe.write("%s\n" % text)
        # NOTE. Without this the tagger will hang. Do not try to make this
        # shorter, I think it may need at least a space, but I have no idea why.
        pipe.write("%s\n.\ndummy sentence\n.\n" % END_TEXT)
        pipe.flush()
