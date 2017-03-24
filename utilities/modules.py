"""

Nothing but a listing of all Tarsqi Python modules.

Provides a variable named MODULES that contains all Tarsqi modules that are
needed as input to the analysis and documentation creation scripts.

"""

import path
import tarsqi

import components.blinker.compare
import components.blinker.main
import components.blinker.wrapper

import components.classifier.wrapper
import components.classifier.vectors

import components.common_modules.chunks
import components.common_modules.component
import components.common_modules.constituent
import components.common_modules.tree
import components.common_modules.sentence
import components.common_modules.tags
import components.common_modules.tokens

import components.evita.bayes
import components.evita.event
import components.evita.features
import components.evita.main
import components.evita.rule
import components.evita.wrapper

import components.gutime.wrapper

import components.merging.wrapper

import components.preprocessing.abbreviation
import components.preprocessing.chunker
import components.preprocessing.tokenizer
import components.preprocessing.wrapper

import components.s2t.main
import components.s2t.wrapper

import components.slinket.main
import components.slinket.wrapper

import components.merging.wrapper
import components.merging.sputlink.main
import components.merging.sputlink.graph
import components.merging.sputlink.objects
import components.merging.sputlink.utils

import docmodel.main
import docmodel.document
import docmodel.docstructure_parser
import docmodel.metadata_parser
import docmodel.source_parser

import library.classifier.create_model
import library.classifier.create_vectors

import utilities.mallet
import utilities.binsearch
import utilities.logger
import utilities.stemmer


MODULES = [

    tarsqi,

    components.blinker.compare,
    components.blinker.main,
    components.blinker.wrapper,

    components.classifier.vectors,
    components.classifier.wrapper,

    components.common_modules.chunks,
    components.common_modules.component,
    components.common_modules.constituent,
    components.common_modules.tree,
    components.common_modules.sentence,
    components.common_modules.tags,
    components.common_modules.tokens,

    components.evita.bayes,
    components.evita.event,
    components.evita.features,
    components.evita.main,
    components.evita.rule,
    components.evita.wrapper,

    components.gutime.wrapper,
    # components.gutime.btime,

    components.merging.sputlink.main,
    components.merging.sputlink.graph,
    components.merging.sputlink.objects,
    components.merging.sputlink.utils,
    components.merging.wrapper,

    components.preprocessing.abbreviation,
    components.preprocessing.chunker,
    components.preprocessing.tokenizer,
    components.preprocessing.wrapper,

    components.s2t.main,
    components.s2t.wrapper,

    components.slinket.main,
    components.slinket.wrapper,

    docmodel.document,
    docmodel.docstructure_parser,
    docmodel.main,
    docmodel.metadata_parser,
    docmodel.source_parser,

    library.classifier.create_model,
    library.classifier.create_vectors,

    utilities.binsearch,
    utilities.logger,
    utilities.mallet,
    utilities.stemmer,
]
