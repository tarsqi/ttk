"""

Nothing but a listing of all Tarsqi Python modules.

Provides a variable named MODULES that contains all Tarsqi modules that are needed as
input to the analysis and documentation creation scripts.

"""

import tarsqi

import components.arglinker.wrapper
import components.arglinker.main

import components.blinker.compare
import components.blinker.main
import components.blinker.wrapper

import components.classifier.wrapper

import components.common_modules.chunks
import components.common_modules.component
import components.common_modules.constituent
import components.common_modules.document
import components.common_modules.sentence
import components.common_modules.tags
import components.common_modules.tokens

import components.evita.bayes
import components.evita.event
import components.evita.gramChunk
import components.evita.main
import components.evita.rule
import components.evita.wrapper

import components.gutime.wrapper

import components.merging.wrapper

import components.preprocessing.abbreviation
import components.preprocessing.tokenizer
import components.preprocessing.wrapper

import components.s2t.main
import components.s2t.wrapper

import components.slinket.main
import components.slinket.wrapper

import demo.display

import docmodel.main
import docmodel.document
import docmodel.parsers
import docmodel.xml_parser
import docmodel.source_parser

import utilities.binsearch
import utilities.converter
import utilities.logger
import utilities.porterstemmer
import utilities.xml_utils

import utilities.sputlink.main
import utilities.sputlink.graph
import utilities.sputlink.objects
import utilities.sputlink.utils


MODULES = [
    
    tarsqi,

    components.arglinker.wrapper,
    components.arglinker.main,

    components.blinker.compare,
    components.blinker.main,
    components.blinker.wrapper,

    components.classifier.wrapper,

    components.common_modules.chunks,
    components.common_modules.component,
    components.common_modules.constituent,
    components.common_modules.document,
    components.common_modules.sentence,
    components.common_modules.tags,
    components.common_modules.tokens,

    components.evita.bayes,
    components.evita.event,
    components.evita.gramChunk,
    components.evita.main,
    components.evita.rule,
    components.evita.wrapper,

    components.gutime.wrapper,
    #components.gutime.btime,

    components.merging.wrapper,
    
    components.preprocessing.abbreviation,
    components.preprocessing.tokenizer,
    components.preprocessing.wrapper,

    components.s2t.main,
    components.s2t.wrapper,

    components.slinket.main,
    components.slinket.wrapper,

    demo.display,
    
    docmodel.main,
    docmodel.document,
    docmodel.parsers,
    docmodel.xml_parser,
    docmodel.source_parser,

    utilities.binsearch,
    utilities.converter,
    utilities.logger,
    utilities.porterstemmer,
    utilities.xml_utils,

    utilities.sputlink.main,
    utilities.sputlink.graph,
    utilities.sputlink.objects,
    utilities.sputlink.utils
    ]

