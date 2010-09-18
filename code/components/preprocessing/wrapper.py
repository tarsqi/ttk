"""

Contains the wrapper for all preprocessing components.

"""

import os
from time import time
from types import StringType, TupleType

from ttk_path import TTK_ROOT
from docmodel.xml_parser import XmlDocElement
from library.tarsqi_constants import PREPROCESSOR
from components.preprocessing.tokenizer import tokenize_file
from components.preprocessing.tokenizer import tokenize_string
from components.preprocessing.chunker import chunk_sentences
from treetaggerwrapper import TreeTagger

from utilities import logger
from formatConversor import verticalize_text
from formatConversor import normalizeXML
from formatConversor import normalizePOS



class PreprocessorWrapper:
    
    """Wrapper for the preprocessing components."""
    

    def __init__(self, document):

        """Calls __init__ of the base class and sets component_name."""

        self.component_name = PREPROCESSOR
        self.document = document
        self.xmldoc = document.xmldoc
        self.treetagger_dir = self.document.parameters.get('treetagger')
        self.treetagger = TreeTagger(TAGLANG='en', TAGDIR=self.treetagger_dir)

        
    def process(self):

        """Retrieve the slices from the XmlDocument and hand these slices as strings to
        the preprocessing chain. The tokenizer returns a string, the tagger a list of
        sentences, which the chunker adds chunk tags to. Slices will be updated with the
        chunker results. If a slice contains tags then they will be stripped out and
        disappear."""

        begin_time = time()
        text = self.xmldoc[0].collect_text_content()
        text = self.tokenize_text(text)
        text = self.tag_text(text)
        text = self.chunk_text(text)
        update_xmldoc(self.xmldoc, text)
        #self.document.xmldoc = self.xmldoc
        logger.info("%s DONE, processing time was %.3f seconds" %
                    (self.component_name, time() - begin_time))

        
    def tokenize_text(self, string):

        """Takes a string and returns a tokenized string in a one-line-per-sentence
        format."""

        btime = time()
        tokenized_string = tokenize_string(string, format='text')
        logger.info("tokenizer processing time: %.3f seconds" % (time() - btime))
        return tokenized_string


    def tag_text(self, string):

        """Takes a string and returns a list of sentences. Each sentence is list of tuples
        of token, part-of-speech and lemma."""
    
        btime = time()
        vertical_string = verticalize_text(string)
        taggedItems = self.treetagger.TagText(text=vertical_string,tagonly=True)
        text = []
        current_sentence = []
        for item in taggedItems:
            if item == '<s>':
                current_sentence = []
                text.append(current_sentence)
            elif item[0] == '<' and item[-1] == '>':
                # not quite sure what these are for, probably tags that
                # the TreeTagger leaves alone
                current_sentence.append((item,'SYM',item))
            else:
                (tok, pos, stem) = item.split("\t")
                pos = normalizePOS(pos)
                current_sentence.append((tok, pos, stem))
        logger.info("tagger processing time: %.3f seconds" % (time() - btime))
        return text


    def chunk_text(self, text):

        """Takes a list of sentences and return the same sentences with chunk tags
        inserted. May need to do something with things like &, <, >, and others, see
        xml_utils.protect_text."""
    
        btime = time()
        chunked_text = chunk_sentences(text)
        logger.info("chunker processing time: %.3f seconds" % (time() - btime))
        return chunked_text




def update_xmldoc(xmldoc, text):

    """Updates the xmldoc with the text that is the result of all preprocessing. At the
    onset, the xmldoc has only three elements: a TEXT opening tag, character data, and a
    TEXT closing tag. The character data element is replaced with a list of elements,
    including lex tags, s tags, chunk tags and character data for all tokens."""

    first_element = xmldoc.elements[0]
    last_element = first_element.get_closing_tag()
    first_element.next = last_element
    last_element.previous = first_element
    
    lid = 0
    for sentence in text:
        last_element.insert_element_before( XmlDocElement('\n', data=True) )
        last_element.insert_element_before( XmlDocElement('<s>', tag='s', attrs={}) )
        for token in sentence:
            if type(token) == StringType:
                add_chunktag(last_element, token)
            elif type(token) == TupleType:
                add_token(last_element, token, lid)
                lid += 1
            else:
                logger.warn('Unexpected token type')
        last_element.insert_element_before( XmlDocElement('</s>', tag='s') )

    last_element.insert_element_before( XmlDocElement('\n', data=True) )


def add_chunktag(element, token):

    """Add a chunk tag before the XmlDocElement given."""
    
    tag = token.strip('</>')
    if token.startswith('</'):
        element.insert_element_before( XmlDocElement(token, tag=tag) )
    elif token.startswith('<'):
        element.insert_element_before( XmlDocElement(token, tag=tag, attrs={}) )
    else:
        logger.warn('Unexpected element in chunked text')
    
    
def add_token(element, token, lid):
    
    """Add a token, with its opening and closing lex tags, before the
    XmlDocElement given."""

    (tok, pos, lemma) = token
    if lemma == '<unknown>':
        lemma = tok
    element.insert_element_before(
        XmlDocElement('<lex lid = "l'+str(lid)+'" pos="'+pos+'" lemma="'+lemma+'">',
                      tag='lex',
                      attrs={'lid': "l%d" % lid, 'pos': pos, 'lemma': lemma}) )
    element.insert_element_before( XmlDocElement(tok, data=True) )
    element.insert_element_before( XmlDocElement('</lex>', tag='lex') )
    element.insert_element_before( XmlDocElement(' ', data=True) )
