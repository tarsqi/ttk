"""

Initialization of parsers responsible for document-level parsing.

This module is responsible for creating document source parsers. That is, parsers that
take an instance of DocSource and create an instance of Document (now still called
DocumentPlus to avoid confusion with the still existing class Document, which shall be
renamed into Text).

"""

import os

from docmodel import model
from utilities import logger

from docmodel.general import DefaultParser

from library.tarsqi_constants import PREPROCESSOR, GUTIME, EVITA, SLINKET, S2T
from library.tarsqi_constants import CLASSIFIER, BLINKER, LINK_MERGER, ARGLINKER


PARSERS = {
    'simple-xml': DefaultParser,
    'timebank': DefaultParser,
    'atee': DefaultParser,
    'rte3': DefaultParser }

DEFAULT_PIPELINE = [ PREPROCESSOR, GUTIME, EVITA, SLINKET, S2T,
                     BLINKER, CLASSIFIER, LINK_MERGER ]



def create_parser(genre):

    """Return a document parser. Should include some additional setup of the parser, where
    depending on the genre and perhaps other future arguments some aspects of the parser
    class are set."""
    
    parser = PARSERS.get(genre, DefaultParser)
    return parser()


def get_default_pipeline(genre):

    """Now always returns the same but can be used for genre-specific pipelines."""
    
    return DEFAULT_PIPELINE




"""

THE REST IS ALL OLD CRAP, BUT PARTS OF IT MAY BE REUSED

"""



class DocumentModelInitializer:

    """Class that is used solely to set up the document model instance variables on a
    tarsqi instance. It takes a Tarsqi instance and sets up the right docement
    model functionality on it, given the data source and the processing options.

    Instance variables:
       dsi_to_docmodelconstructor - a mapping from strings to bound methods
    """

    def __init__(self):
        
        """Register all data source identifiers and link them to a constructor in the
        dsi_to_docmodelconstructor dictionary."""

        self.dsi_to_docmodelconstructor = {
            'simple-xml': self._setup_docmodel_simple_xml,
            'timebank': self._setup_docmodel_timebank,
            'atee': self._setup_docmodel_atee,
            'rte3': self._setup_docmodel_rte }
            

    def setup_docmodel(self, tarsqi_instance):

        """Initialize the document_model instance variable of a Tarsqi instance, using its
        data source identifier and processing options.
        
        Arguments:
           tarsqi_instance - a Tarsqi instance
        
        No return value."""

        data_source_identifier = tarsqi_instance.data_source_identifier

        constructor = self.dsi_to_docmodelconstructor.get(data_source_identifier, None)
        try:
            constructor(tarsqi_instance)
        except TypeError, e:
            # log error and use simple-xml as a default
            logger.error("Unknown data source identifier, using simple-xml")
            tarsqi_instance.data_source_identifier = 'simple-xml'
            data_source_identifier = tarsqi_instance.data_source_identifier
            self._setup_docmodel_simple_xml(tarsqi_instance)
        
        # copy content_tag from document model for convenience
        tarsqi_instance.content_tag = tarsqi_instance.document_model.get_content_tag()


    def _setup_docmodel_simple_xml(self, tarsqi_instance):

        """Sets up the document model for the Tarsqi instance if the data source is
        'simple-xml' or 'simple-xml-preprocessed'. Uses SimpleXmlModel and
        MetaDataParser_TimeBank and sets the content tag to 'TEXT'. Differences in
        preprocessing chains are handled when the pipeline is set. User options that can
        override default settings will be taken into consideration in sub methods. Is now
        identical to the timebank document model but will need to get a more default
        MetaData Parser. Takes a Tarsqi instance and has no return value."""

        self._setup_docmodel(tarsqi_instance,
                             model.SimpleXmlModel(tarsqi_instance.input),
                             'TEXT',
                             model.MetaDataParser_SimpleXml())

        
    def _setup_docmodel_timebank(self, tarsqi_instance):

        """Sets up the document model for the Tarsqi instance if the data source is
        'timebank-source' or 'timebank-preprocessed'. Uses SimpleXmlModel and
        MetaDataParser_TimeBank, and sets the content tag to 'TEXT'. Differences in
        preprocessing chains are handled when the pipeline is set. Takes a Tarsqi
        instance and has no return value."""

        self._setup_docmodel(tarsqi_instance,
                             model.SimpleXmlModel(tarsqi_instance.input),
                             'TEXT',
                             model.MetaDataParser_TimeBank())

        
    def _setup_docmodel_rte(self, tarsqi_instance):

        """Sets up the document model for the Tarsqi instance if the data source is
        'RTE3'. Uses SimpleXmlModel and MetaDataParser_RTE, and sets the content tag to
        'PAIR'. Takes a Tarsqi instance and has no return value."""

        self._setup_docmodel(tarsqi_instance,
                             model.SimpleXmlModel(tarsqi_instance.input),
                             'pair',
                             model.MetaDataParser_RTE())

        
    def _setup_docmodel_atee(self, tarsqi_instance):

        """Sets up the document model for the Tarsqi instance if the data source is
        'ATEE'. Uses SimpleXmlModel and MetaDataParser_ATEE, and sets the content tag to
        'TailParas'. Takes a Tarsqi instance and has no return value."""

        self._setup_docmodel(tarsqi_instance,
                             model.SimpleXmlModel(tarsqi_instance.input),
                             'TailParas',
                             model.MetaDataParser_ATEE())

        
    def _setup_docmodel(self, tarsqi_instance, docmodel, content_tag, metadata_parser):

        """Initialize the document model and set its metadata parser. Then set the content
        tag and the pipeline, in both cases default values from the data source identifier
        can be overruled by user options."""

        tarsqi_instance.document_model = docmodel
        tarsqi_instance.document_model.set_metadata_parser(metadata_parser)
        self._set_content_tag(content_tag, tarsqi_instance)

        
    def _set_content_tag(self, default_tag, tarsqi_instance):

        """Sets the content tag using the procided default, overriding it if a user option
        was specified."""

        tarsqi_instance.document_model.set_content_tag(default_tag)
        content_tag = tarsqi_instance.getopt_content_tag()
        if content_tag:
            tarsqi_instance.document_model.set_content_tag(content_tag)
