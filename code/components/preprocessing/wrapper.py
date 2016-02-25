"""

Contains the wrapper for all preprocessing components.

"""

import os
from time import time
from types import StringType, TupleType
from xml.sax.saxutils import escape, quoteattr

from utilities import logger
#from docmodel.source_parser import Tag
from docmodel.document import Tag
from library.tarsqi_constants import PREPROCESSOR

from components.preprocessing.tokenizer import Tokenizer
from components.preprocessing.chunker import chunk_sentences
from treetaggerwrapper import TreeTagger


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


treetagger = None

def initialize_treetagger(treetagger_dir):
    global treetagger
    if treetagger is None:
        treetagger = TreeTagger(TAGLANG='en', TAGDIR=treetagger_dir)
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
    """The tokenizer works on isolated strings, adding offsets relative to the beginning
    of the string. But for the lex tags we need to relate the offset to the beginning of
    the file, not to the beginning of some random string. This procedure is used to
    increment offsets on instances of TokenizedLex."""
    for token_string, token_object in tokens:
        # skip the ('<s>', None) pairs
        if token_object is not None:
            token_object.begin += offset
            token_object.end += offset


class PreprocessorWrapper:

    """Wrapper for the preprocessing components."""

    def __init__(self, tarsqidocument):
        """Set component_name, add the TarsqiDocument and initialize the TreeTagger."""
        self.component_name = PREPROCESSOR
        self.document = tarsqidocument
        self.treetagger_dir = self.document.options.getopt('treetagger')
        self.treetagger = initialize_treetagger(self.treetagger_dir)
        self.tokenize_time = 0
        self.tag_time = 0
        self.chunk_time = 0

    def process(self):
        """Retrieve the elements from the TarsqiDocument and hand these as strings to the
        preprocessing chain. The result is a shallow tree with sentences and tokens. These
        are inserted into the element's tarsqi_tags TagRepositories."""
        TagId.reset()
        for element in self.document.elements:
            tokens = self.tokenize_text(element.get_text())
            adjust_lex_offsets(tokens, element.begin)
            text = self.tag_text(tokens)
            # TODO: add some code to get lemmas when the TreeTagger just gets
            # <unknown>, see https://github.com/tarsqi/ttk/issues/5
            text = self.chunk_text(text)
            export(text, element)
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
        """Takes a string and returns a list of sentences. Each sentence is a list of tuples
        of token, part-of-speech and lemma."""
        t1 = time()
        vertical_string = "\n".join([t[0] for t in tokens])
        # this avoids handler warning if input is empty
        if not vertical_string.strip():
            vertical_string = '<s>'
        # treetagger does not accept a unicode string, so encode in utf-8
        taggedItems = self.call_treetagger(vertical_string.encode('utf-8'))
        text = self.create_text_from_tokens_and_tags(tokens, taggedItems)
        self.tag_time += time() - t1
        return text

    def chunk_text(self, text):
        """Takes a list of sentences and return the same sentences with chunk tags
        inserted. May need to do something with things like &, <, >, and others."""
        t1 = time()
        chunked_text = chunk_sentences(text)
        self.chunk_time += time() - t1
        return chunked_text

    def call_treetagger(self, vertical_string):
        """Call the TreeTagger on the vertical string and retrun the result."""
        return self.treetagger.TagText(text=vertical_string, tagonly=True,
                                       notagurl=True, notagemail=True,
                                       notagip=False,notagdns=False)

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
                # not quite sure what these are for, probably tags that the TreeTagger
                # leaves alone
                current_sentence.append((item[0], 'SYM', item[0], lex.begin, lex.end))
            else:
                (tok, pos, stem) = item.split("\t")
                pos = normalizePOS(pos)
                current_sentence.append((tok, pos, stem, lex.begin, lex.end))
        return text    


def export(text, tarsqi_element):
    """Export preprocessing information to the tag repository. Updates the
    TagRepository with the text that is the result of preprocessing."""

    ctag = None

    for sentence in text:

        stag = Tag(TagId.next('s'), 's', None, None, {})

        for token in sentence:

            if type(token) == StringType and token.startswith('<') and token.endswith('>'):
                if not token.startswith('</'):
                    ctag = Tag(TagId.next('c'), token[1:-1], None, None, {})
                else:
                    ctag.end = last_ltag.end
                    tarsqi_element.tarsqi_tags.append(ctag)
                    ctag = None

            elif type(token) == TupleType:
                ltag = Tag(TagId.next('l'), 'lex', token[3], token[4],
                           { 'lemma': token[2], 'pos': token[1], 'text': token[0] })
                tarsqi_element.tarsqi_tags.append(ltag)
                if stag.begin is None:
                    stag.begin = token[3]
                if ctag is not None and ctag.begin is None:
                    ctag.begin = ltag.begin
                last_end_offset = token[4]
                last_ltag = ltag

            else:
                logger.warn('Unexpected token type')

        stag.end = last_ltag.end
        tarsqi_element.tarsqi_tags.append(stag)

    # indexing is needed because we bypassed the add_tag method on TagRepository
    # and instead directly appended to the tags list
    tarsqi_element.tarsqi_tags.index()
