"""

Contains the wrapper for all preprocessing components.

"""

import os
from time import time
from types import StringType, TupleType
from xml.sax.saxutils import escape, quoteattr

from ttk_path import TTK_ROOT
from utilities import logger
from docmodel.xml_parser import XmlDocElement
from library.tarsqi_constants import PREPROCESSOR
from components.preprocessing.tokenizer import Tokenizer
from components.preprocessing.chunker import chunk_sentences
from treetaggerwrapper import TreeTagger


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


class PreprocessorWrapper:
    
    """Wrapper for the preprocessing components."""
    

    def __init__(self, document):
        """Set component_name and initialize TreeTagger."""
        self.component_name = PREPROCESSOR
        self.document = document
        self.xmldoc = document.xmldoc
        self.treetagger_dir = self.document.getopt('treetagger')
        self.treetagger = initialize_treetagger(self.treetagger_dir)
        
    def process(self):
        """Retrieve the elements from the tarsqiDocument and hand these as strings to the
        preprocessing chain. The result is shallow tree with sentences and tokens. These
        are inserted into the element's xmldoc. Note that for simple documents with just
        one element, updating the xmldoc in the element also updates the xmldoc in the
        TarsqiDocument."""
        for element in self.document.elements:
            tokens = self.tokenize_text(element.text)
            text = self.tag_text(tokens)
            text = self.chunk_text(text)
            for x in text: print x
            update_xmldoc(element.xmldoc, text)
            update_tags(element.tarsqi_tags, element.xmldoc)
            
    def tokenize_text(self, string):
        """Takes a unicode string and returns a list of objects, where each object is a
        pair of tokenized string and a TokenizedLex instance. The tokenized string can be
        '<s>', in which case the second element of the pair is None instead of a
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


def update_xmldoc(xmldoc, text):

    """Updates the xmldoc with the text that is the result of all preprocessing. At the
    onset, the xmldoc has only three elements: TEXT opening tag, character data, and TEXT
    closing tag. The character data element is replaced with a list of elements, including
    lex tags, s tags, chunk tags and character data for all tokens."""

    first_element = xmldoc.elements[0]
    last_element = first_element.get_closing_tag()
    first_element.next = last_element
    last_element.previous = first_element

    (sid, lid, cid) = (0, 0, 0)
    
    for sentence in text:

        sid += 1
        last_element.insert_element_before( XmlDocElement('\n', data=True) )
        last_element.insert_element_before( XmlDocElement("<s>", tag='s', attrs={}) )

        # TODO: it would be desirable to use the following and add identifiers to
        # sentences, but with it the code to merge in timexes fails, wait with this till
        # we have BTime
        #
        # last_element.insert_element_before( XmlDocElement("<s sid=\"s%d\">" % sid,
        #                                                   tag='s',
        #                                                   attrs={'sid': "s%d" % sid}) )

        for token in sentence:
            if type(token) == StringType:
                if token.startswith('<') and not token.startswith('</'): cid += 1
                add_chunktag(last_element, token, cid)
            elif type(token) == TupleType:
                lid += 1
                add_token(last_element, token, lid)
            else:
                logger.warn('Unexpected token type')
                
        last_element.insert_element_before( XmlDocElement('</s>', tag='s') )

    last_element.insert_element_before( XmlDocElement('\n', data=True) )
    xmldoc.reset()


def add_chunktag(element, token, cid):

    """Add a chunk tag before the XmlDocElement given."""
    
    tag = token.strip('</>')
    if token.startswith('</'):
        element.insert_element_before( XmlDocElement(token, tag=tag) )
    elif token.startswith('<'):
        # see comment in previous routine
        #token = token[:-1] + " cid=\"c%d\">" % cid
        element.insert_element_before( XmlDocElement(token, tag=tag, attrs={}) )
    else:
        logger.warn('Unexpected element in chunked text')
    
    
def add_token(element, token, lid):
    
    """Add a token, with its opening and closing lex tags, before the XmlDocElement
    given."""

    (tok, pos, lemma, begin, end) = token
    if lemma == '<unknown>': lemma = tok
    lid = "l%d" % lid

    lex_string = "<lex lid=\"%s\" pos=%s lemma=%s begin=\"%d\" end=\"%d\">" % \
                 (lid, quoteattr(pos), quoteattr(lemma), begin, end)
    lex_attrs={'lid': lid, 'pos': pos, 'lemma': lemma, 'begin': begin, 'end': end }
                      
    element.insert_element_before( XmlDocElement(lex_string, tag='lex', attrs=lex_attrs) )
    element.insert_element_before( XmlDocElement(tok, data=True) )
    element.insert_element_before( XmlDocElement('</lex>', tag='lex') )
    element.insert_element_before( XmlDocElement(' ', data=True) )


def update_tags(tag_repository, xml_doc):

    """Update the TagRepository using the XmlDocument. Adds all sentence, chunk and lex
    tags. May want to do this in one fell swoop for all added tags later in the processing
    chain."""

    def get_offsets(element):
        """Return tuple with tagname, begin and end for the element. Begin and end are
        calcualted from the first and last contained lex tags lex tags of the element,
        return None if there are no contained lex tags."""
        tags = [t for t in element.collect_contained_tags() if t.tag == 'lex']
        if tags:
            begin = tags[0].attrs['begin']
            end = tags[-1].attrs['end']
            return (element.get_tag(), begin, end)
        return None

    for element in xml_doc:
        if element.is_opening_tag():
            tagname = element.get_tag()
            if tagname == 'lex':
                (begin, end) = (element.attrs['begin'], element.attrs['end'])
                tag_specification = ('lex', begin, end, element.attrs)
                tag_repository.add_tag(tag_specification)
            if tagname in ['s', 'NG', 'VG']:
                tag_specification = get_offsets(element) + ({},)
                if tag_specification is not None:
                    # throw away sentence and chunk tags that are empty
                    tag_repository.add_tag(tag_specification)

    tag_repository.index()
