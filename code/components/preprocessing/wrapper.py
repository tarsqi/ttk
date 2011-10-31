"""

Contains the wrapper for all preprocessing components.

"""

import os
from time import time
from types import StringType, TupleType

from ttk_path import TTK_ROOT
from utilities import logger
from docmodel.source_parser import Tag
from library.tarsqi_constants import PREPROCESSOR
from components.preprocessing.tokenizer import Tokenizer
from components.preprocessing.chunker import chunk_sentences
from treetaggerwrapper import TreeTagger


# ensure unique identifiers
LEX_ID = 0
CHUNK_ID = 0
SENT_ID = 0

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
        """Set component_name and initialize TreeTagger."""
        self.component_name = PREPROCESSOR
        self.document = document
        self.treetagger_dir = self.document.getopt('treetagger')
        self.treetagger = initialize_treetagger(self.treetagger_dir)
        
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
            export(text, element.tarsqi_tags)
            
    def tokenize_text(self, string):
        """Takes a unicode string and returns a list of objects, where each object is a
        pair of a tokenized string and a TokenizedLex instance. The tokenized string can
        be '<s>', in which case the second element of the pair is None instead of a
        TokenizedLex."""
        t1 = time()
        tokenizer = Tokenizer(string)
        tokenized_text = tokenizer.tokenize_text()
        #tokenized_text.print_as_xmlstring()
        pairs = tokenized_text.as_pairs()
        logger.info("tokenizer processing time: %.3f seconds" % (time() - t1))
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
        logger.info("tagger processing time: %.3f seconds" % (time() - t1))
        return text

    def chunk_text(self, text):
        """Takes a list of sentences and return the same sentences with chunk tags
        inserted. May need to do something with things like &, <, >, and others, see
        xml_utils.protect_text."""
        t1 = time()
        chunked_text = chunk_sentences(text)
        logger.info("chunker processing time: %.3f seconds" % (time() - t1))
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
                # not quite sure what these are for, probably tags that
                # the TreeTagger leaves alone
                current_sentence.append((item[0], 'SYM', item[0], lex.begin, lex.end))
            else:
                (tok, pos, stem) = item.split("\t")
                pos = normalizePOS(pos)
                current_sentence.append((tok, pos, stem, lex.begin, lex.end))
        return text    



def export(text, tag_repository):

    """Updates the TagRepository with the text that is the result of preprocessing."""

    global LEX_ID, CHUNK_ID, SENT_ID
    ctag = None

    for sentence in text:

        SENT_ID += 1
        stag = Tag(SENT_ID, 's', None, None, {})

        for token in sentence:

            if type(token) == StringType and token.startswith('<') and token.endswith('>'):
                if not token.startswith('</'):
                    CHUNK_ID += 1
                    ctag = Tag(CHUNK_ID, token[1:-1], None, None, {})
                else:
                    ctag.end = last_ltag.end
                    ctag.nodes.append("%s%d" % (last_ltag.name, last_ltag.id))
                    tag_repository.append(ctag)
                    ctag = None

            elif type(token) == TupleType:
                LEX_ID += 1
                ltag = Tag(LEX_ID, 'lex', token[3], token[4], { 'lemma': token[2], 'pos': token[1] })
                tag_repository.append(ltag)
                if stag.begin is None:
                    stag.begin = token[3]
                    stag.nodes.append("%s%d" % (ltag.name, ltag.id))
                if ctag is not None and ctag.begin is None:
                    ctag.begin = ltag.begin
                    ctag.nodes.append("%s%d" % (ltag.name, ltag.id))
                last_end_offset = token[4]
                last_ltag = ltag

            else:
                logger.warn('Unexpected token type')

        stag.end = last_ltag.end
        stag.nodes.append("%s%d" % (last_ltag.name, last_ltag.id))
        tag_repository.append(stag)

    tag_repository.index()
