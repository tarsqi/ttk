import re

"""==============================================

Variables for TimeML tags, attributes and  values

Author: Roser
Last Modified: April 14, 2005
==============================================="""

# TimeBank chunking
# =================

SENTENCE = 's'
NOUNCHUNK = 'NG'
VERBCHUNK = 'VG'
TOKEN = 'lex'
LID = 'lid'
POS = 'pos'


# POS Tags
# ========

POS_ADJ = 'JJ'
POS_CD = 'CD'
POS_PREP = 'IN'


# TimeBank Processing
# ===================

# Classes declared in Chunk.py and used by ppParser.py, eventParser.py:
ConstituentClassNames = ['Constituent', 'Chunk', 'NounChunk', 'VerbChunk', 'Token', 'AdjectiveToken']
ChunkClassNames = ['Chunk', 'NounChunk', 'VerbChunk']
EventConstituentClassNames = ChunkClassNames + ['AdjectiveToken'] 

FORM = 'form'



# TimeML spec
# ===========

TIMEML = 'TimeML'

EVENT = 'EVENT'
MAKEINSTANCE = 'MAKEINSTANCE'
EID = 'eid'
CLASS = 'class'
STEM = 'stem'

TIMEX = 'TIMEX3'
TID = 'tid'

SIGNAL = 'SIGNAL'

INSTANCE = 'MAKEINSTANCE'
EVENTID = 'eventID'
EIID = 'eiid'
EPOS = 'epos' #NF_MORPH = 'nf_morph'
TENSE = 'tense'
ASPECT = 'aspect'
MOD = 'modality'
POL = 'polarity'
NO_FINITE = ['PRESPART', 'PASTPART', 'INFINITIVE']
FINITE = ['PRESENT', 'PAST', 'FUTURE']

LINK = re.compile('(S|T|A)LINK')
TLINK = 'TLINK'
SLINK = 'SLINK'
ALINK = 'ALINK'

RELTYPE = 'relType'
EVENT_INSTANCE_ID = 'eventInstanceID'
TIME_ID = 'timeID'
SUBORDINATED_EVENT_INSTANCE = 'subordinatedEventInstance'
RELATED_TO_EVENT_INSTANCE = 'relatedToEventInstance'
RELATED_TO_TIME = 'relatedToTime'
CONFIDENCE = 'confidence'
ORIGIN = 'origin'
SYNTAX = 'syntax'

NOUN = 'NOUN'
ADJECTIVE = 'ADJECTIVE'
VERB = 'VERB'
NONE = 'NONE'

EMPTY_TAGS = ['MAKEINSTANCE', 'TLINK', 'SLINK', 'ALINK']

COUNTER_FACTIVE = 'COUNTER_FACTIVE'
FACTIVE = "FACTIVE"
MODAL = "MODAL"
CONDITIONAL = "CONDITIONAL"
EVIDENTIAL = "EVIDENTIAL"
NEG_EVIDENTIAL = "NEG_EVIDENTIAL"

INIT = 'INITIATES'
TERM = 'TERMINATES'
CULM = 'CULMINATES'
CONT = 'CONTINUES'
REINIT = 'REINITIATES'
