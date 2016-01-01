"""

Contains the wrapper for all preprocessing components.

"""

import os
from time import time
from types import StringType, TupleType
from xml.sax.saxutils import escape, quoteattr

from utilities import logger
from docmodel.source_parser import Tag
from library.tarsqi_constants import PREPROCESSOR

from components.common_modules.document import Document
from components.common_modules.sentence import Sentence
from components.common_modules.chunks import NounChunk, VerbChunk
from components.common_modules.tokens import Token, AdjectiveToken

from components.preprocessing.tokenizer import Tokenizer
from components.preprocessing.chunker import chunk_sentences
from treetaggerwrapper import TreeTagger



class TagId:
    """Class to provide fresh identifers for lex, ng, vg and s tags."""
    ids = { 's': 0, 'c': 0, 'l': 0 }
    @classmethod
    def next(cls, prefix):
        cls.ids[prefix] += 1
        return "%s%d" % (prefix, cls.ids[prefix])


treetagger = None

def initialize_treetagger(treetagger_dir):
    global treetagger
    if treetagger is None:
        treetagger = TreeTagger(TAGLANG='en', TAGDIR=treetagger_dir)
    return treetagger

def normalizePOS(pos):
    """Some simple modifications of the TreeTagger POS tags."""
    if pos == 'SENT':
        pos ='.'
    elif pos[0] == 'V':
        if pos[1] in ['V', 'H']:
            if len(pos) > 2:
                rest = pos[2:]
            else: rest = ''
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
    for token in tokens:
        if token[1] is None:  # skip the s tags
            continue
        token[1].begin += offset
        token[1].end += offset


class PreprocessorWrapper:
    
    """Wrapper for the preprocessing components."""

    def __init__(self, document):
        """Set component_name, add the TarsqiDocument and initialize the TreeTagger."""
        self.component_name = PREPROCESSOR
        self.document = document
        self.treetagger_dir = self.document.getopt('treetagger')
        self.treetagger = initialize_treetagger(self.treetagger_dir)
        self.tokenize_time = 0
        self.tag_time = 0
        self.chunk_time = 0

    def process(self):
        """Retrieve the elements from the tarsqiDocument and hand these as strings to the
        preprocessing chain. The result is a shallow tree with sentences and tokens. These
        are inserted into the element's xmldoc. TODO: remove xmldoc. Note that for simple
        documents with just one element, updating the xmldoc in the element also updates
        the xmldoc in the TarsqiDocument."""
        for element in self.document.elements:
            tokens = self.tokenize_text(element.get_text())
            adjust_lex_offsets(tokens, element.begin)
            text = self.tag_text(tokens)
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
    """Export preprocessing information to the tag repository ad the doctree."""
    export_text_to_tags(text, tarsqi_element)
    export_tags_to_doctree(tarsqi_element)
    

def export_text_to_tags(text, tarsqi_element):
    """Updates the TagRepository with the text that is the result of preprocessing."""

    ctag = None

    for sentence in text:

        stag = Tag(TagId.next('s'), 's', None, None, {})

        for token in sentence:

            if type(token) == StringType and token.startswith('<') and token.endswith('>'):
                if not token.startswith('</'):
                    ctag = Tag(TagId.next('c'), token[1:-1], None, None, {})
                else:
                    ctag.end = last_ltag.end
                    ctag.nodes.append("%s" % (last_ltag.id))
                    tarsqi_element.tarsqi_tags.append(ctag)
                    ctag = None

            elif type(token) == TupleType:
                ltag = Tag(TagId.next('l'), 'lex', token[3], token[4], { 'lemma': token[2], 'pos': token[1] })
                tarsqi_element.tarsqi_tags.append(ltag)
                if stag.begin is None:
                    stag.begin = token[3]
                    stag.nodes.append("%s" % (ltag.id))
                if ctag is not None and ctag.begin is None:
                    ctag.begin = ltag.begin
                    ctag.nodes.append("%s" % (ltag.id))
                last_end_offset = token[4]
                last_ltag = ltag

            else:
                logger.warn('Unexpected token type')

        stag.end = last_ltag.end
        stag.nodes.append("%s" % (last_ltag.id))
        tarsqi_element.tarsqi_tags.append(stag)

    tarsqi_element.tarsqi_tags.index()


def export_tags_to_doctree(tarsqi_element):
    """Build an instance of Document in the doctree variable, using the tags in the
    tarsqi_tags repository."""

    element_name = tarsqi_element.__class__.__name__ + ':' + str(tarsqi_element.id)
    tarsqi_element.doctree = Document(element_name)
    doctree = tarsqi_element.doctree
    tarsqi_doc = tarsqi_element.doc

    currentSentence = Sentence()
    chunks = []

    for t in tarsqi_element.tarsqi_tags.tags:

        if t.name == 's':
            insert_chunks(currentSentence, chunks)
            chunks = []
            doctree.addSentence(currentSentence)
            currentSentence = Sentence()

        elif t.name in ('NG', 'VG'):
            chunks.append(t)

        elif t.name == 'lex':
            p1 = t.begin
            p2 = t.end
            tok = Token(doctree, t.attrs['pos'], t.id)
            tok.text = tarsqi_doc.text(p1,p2)
            currentSentence.add(tok)
            
    #doctree.pretty_print()


def insert_chunks(sentence, chunks):
    """For each chunk, find the lexes that are part of it, add them to the chunk, and
    replace the sequences of lex tags in the sentence woth the chunk."""

    def find_lex_in_sentence(lid):
        idx = 0
        for l in sentence:
            if l.isToken() and l.lid == lid: return idx
            idx += 1
        return -1

    def chunk_class(tag):
        if tag == 'NG': return NounChunk
        if tag == 'VG': return VerbChunk

    for c in chunks:
        lex1 = find_lex_in_sentence(c.nodes[0])
        lex2 = find_lex_in_sentence(c.nodes[-1])
        if c.name in ('NG', 'VG'):
            c_class = chunk_class(c.name)
            chunk = c_class(c.name)
            for i in range(lex1, lex2+1):
                chunk.addToken(sentence[i])
            sentence[lex1:lex2+1] = [chunk]
