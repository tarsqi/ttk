"""feature_rules.py

Library of feature rules to generate some of the grammatical features of a
chunk. Rules are matched to a sequence of Tokens and return a tuple <tense,
aspect, nf_morph> if the match is succesfull.

A rule is a list and has the following fields:

   RULE_NAME, (WORD_SPEC, POS_SPEC){1:7}, FEATURES_TUPLE

A WORD_SPEC or a POS_SPEC is either None or a pair of an operator and an element
that needs to be matched. If the operator is 'in' than the element is a list and
if the operator is '==' then the element is a string. The operator and the
element are used to match to a token in the chunk. Which token this is depends
on the position in the rule of the WORD_SPEC and POS_SPEC.

Rule sets are defined for token sequences from length 1 through 7. The rule list
for a sequence of two tokens has a length of six:

   RULE_NAME, WORD_SPEC_T1, POS_SPEC_T1, WORD_SPEC_T2, POS_SPEC_T2, FEATURES_TUPLE

WORD_SPEC_T1 and POS_SPEC_T1 have to match the word and part-of-speech of the
first token and WORD_SPEC_T2, POS_SPEC_T2 have to match the word and pos of the
second token. Here is an example rule:

    [ 'GR-2-3',
      # Active, 'do' form in present + base form ('do ask')
      ('in', do), ('in', verbsPresent),
      None, ('in', ['VB', 'VBP']),
      ('PRESENT', 'NONE', 'VERB') ]

Note that since the rules are only applied for VerbChunks the nf_morph element
is always 'VERB'.

In this case the first word has to be in the list do (which is defined in forms)
and its part-of-speech has to be in the list verbsPresent (also defined in
forms), and the second word can be any string but its pos has to be VB or VBP.

All rules are exported in the FEATURE_RULES dictionary, which is indexed on the
length of the rule. The rules are used by Evita, where the classes FeatureRule
and VChunkFeatures control application of these rules.

"""


from library.forms import *


grammarRules1 = [ # Length 1 rules

    ['GR-1-1',
     # Active, simple past ('asked')
     None, ('in', verbsPast),
     ('PAST', 'NONE', 'VERB')],

    ['GR-1-2',
     # Active, simple present ('asks')
     None, ('in', verbsPresent),
     ('PRESENT', 'NONE', 'VERB')],

    ['GR-1-3',
     # infinitive ('(to) ask')
     None, ('==', 'VB'),
     ('INFINITIVE', 'NONE', 'VERB')],

    ['GR-1-4',
     # past participle ('asked')
     None, ('==', 'VBN'),
     ('PASTPART', 'NONE', 'VERB')],

    ['GR-1_5',
     # present participle ('asking')
     None, ('==', 'VBG'),
     ('PRESPART', 'NONE', 'VERB')],

    ]


grammarRules2 = [ # Length 2 rules

    ['GR-2-1',
     # Active, future simple ('will ask')
     ('in', futureMod), ('==', 'MD'),
     None, ('in', verbsPresent+['VB']),
     ('FUTURE', 'NONE', 'VERB')],

    ['GR-2-2',
     # Active, modal + base form ('would ask')
     ('in', allMod), ('==', 'MD'),
     None, ('in', verbsPresent+['VB']),
     ('NONE', 'NONE', 'VERB')],

    ['GR-2-3',
     # Active, 'do' form in present + base form ('do ask')
     ('in', do), ('in', verbsPresent),
     None, ('in', ['VB', 'VBP']),
     ('PRESENT', 'NONE', 'VERB')],

    ['GR-2-4',
     # Active, 'do' form in past + base form ('did ask')
     ('in', do), ('in', verbsPast),
     None, ('in', ['VB', 'VBP']),
     ('PAST', 'NONE', 'VERB')],

    ['GR-2-5',
     # Active, present progressive ('is V_ing')
     ('in', be), ('in', verbsPresent),
     None, ('==', 'VBG'),
     ('PRESENT', 'PROGRESSIVE', 'VERB')],

    ['GR-2-6',
     # Active, past progressive ('was V_ing')
     ('in', be), ('in', verbsPast),
     None, ('==', 'VBG'),
     ('PAST', 'PROGRESSIVE', 'VERB')],

    ['GR-2-7',
     # Active, infinitive progressive ('be V_ing')
     ('==', 'be'), ('==', 'VB'),
     None, ('==', 'VBG'),
     ('INFINITIVE', 'PROGRESSIVE', 'VERB')],    

    ['GR-2-8',
     # Active, past. participle progressive ('been V_ing')
     ('==', 'been'), None,
     None, ('==', 'VBG'),
     ('PASTPART', 'PROGRESSIVE', 'VERB')],    

    ['GR-2-9',
     # Active, pres. participle progressive ('being V_ing')
     ('==', 'being'), None,
     None, ('==', 'VBG'),
     ('PRESPART', 'PROGRESSIVE', 'VERB')],    

    ['GR-2-10',
     # Active, present perfective ('has V_en')
     ('in', have), ('in', verbsPresent+['VB']),
     None, ('in', verbsPart),
     ('PRESENT', 'PERFECTIVE', 'VERB')],

    ['GR-2-11',
     # Active, past perfective ('had V_en')
     ('in', have), ('in', verbsPast),
     None, ('in', verbsPart),
     ('PAST', 'PERFECTIVE', 'VERB')],

    ['GR-2-12',
     # Active, infinitive perfective ('have V_en')
     ('==', 'have'), ('==', 'VB'),
     None, ('==', 'VBN'),
     ('INFINITIVE', 'PERFECTIVE', 'VERB')],    

    ['GR-2-13',
     # Active, present participle perfective ('having V_en')
     ('==', 'having'), ('==', 'VBG'),
     None, ('in', verbsPart),
     ('PRESPART', 'PERFECTIVE', 'VERB')],

    ['GR-2-14',
     # Passive, simple past ('was V_en')
     ('in', be), ('in', verbsPast),
     None, ('in', verbsPart),
     ('PAST', 'NONE', 'VERB')],   

    ['GR-2-15',
     # Passive, simple present ('is V_en')
     ('in', be), ('in', verbsPresent),
     None, ('in', verbsPart),
     ('PRESENT', 'NONE', 'VERB')],

    ['GR-2-16',
     # Passive, infinitive ('be V_en': 'for a wish to be fulfilled...')
     ('==', 'be'), None,
     None, ('in', verbsPart),
     ('INFINITIVE', 'NONE', 'VERB')],

    ['GR-2-17',
     # Passive, present participle ('being V_en')
     ('==', 'being'), ('==', 'VBG'),
     None, ('in', verbsPart),
     ('PRESPART', 'NONE', 'VERB')],    

    ['GR-2-18',
     # Passive, past participle ('been V_en')
     ('==', 'been'), ('==', 'VBN'),
     None, ('in', verbsPart),
     ('PASTPART', 'NONE', 'VERB')]

    ]


grammarRules3 = [ # Lenght 3 rules

    ['GR-3-1',
     # Active, modal "have to" Present + base form ('has to ask')
     ('in', have), ('in', verbsPresent),
     ('==', 'to'), ('==', 'TO'),
     None, ('in', verbsBase),
     ('PRESENT', 'NONE', 'VERB')],

    ['GR-3-2',
     # Active, modal "had to" Past + base form ('had to ask')
     ('in', have), ('in', verbsPast), 
     ('==', 'to'), ('==', 'TO'),
     None, ('in', verbsBase),
     ('PAST', 'NONE', 'VERB')],

    ['GR-3-3',
     # Active, modal "have to" infinitive + base form  ('(to) have to ask')
     ('==', 'have'), ('==', 'VB'), 
     ('==', 'to'), ('==', 'TO'),
     None, ('in', verbsBase),
     ('INFINITIVE', 'NONE', 'VERB')],

    ['GR-3-4',
     # Active, modal "have to" presPart + base form ('having to ask')
     ('==', 'having'), None, 
     ('==', 'to'), ('==', 'TO'),
     None, ('in', verbsBase),
     ('PRESPART', 'NONE', 'VERB')],

    ['GR-3-5',
     # Active, fut. progressive ('will be V_ing')
     ('in', futureMod), None,
     ('==', 'be'), None,
     None, ('==', 'VBG'),
     ('FUTURE', 'PROGRESSIVE', 'VERB')],

    ['GR-3-6',
     # Active, modal progressive ('must be V_ing')
     ('in', allMod), None,
     ('==', 'be'), None,
     None, ('==', 'VBG'),
     ('NONE', 'PROGRESSIVE', 'VERB')],

    ['GR-3-7',
     # Active, fut. perfective ('will have V_en')
     ('in', futureMod), None,
     ('==', 'have'), None,
     None, ('in', verbsPart),
     ('FUTURE', 'PERFECTIVE', 'VERB')],

    ['GR-3-8',
     # Active, modal perfective ('must have V_en')
     ('in', allMod), None,
     ('==', 'have'), None,
     None, ('in', verbsPart),
     ('NONE', 'PERFECTIVE', 'VERB')],

    ['GR-3-9',
     # Active, present perfective-progressive ('has been V_ing')
     ('in', have), ('in', verbsPresent+['VB']),
     ('==', 'been'), None,
     None, ('==', 'VBG'),
     ('PRESENT', 'PERFECTIVE_PROGRESSIVE', 'VERB')],

    ['GR-3-10',
     # Active, past perfective-progressive ('had been V_ing')
     ('in', have), ('in', verbsPresent),
     ('==', 'been'), None,
     None, ('==', 'VBG'),
     ('PAST', 'PERFECTIVE_PROGRESSIVE', 'VERB')],

    ['GR-3-11',
     # Active, infinitive perfective-progressive ('(to) have been V_ing')
     ('in', have), ('==', 'VB'),
     ('==', 'been'), None,
     None, ('==', 'VBG'),
     ('INFINITIVE', 'PERFECTIVE_PROGRESSIVE', 'VERB')],

    ['GR-3-12',
     # Passive, modal ('should be V_en')
     ('in', allMod), None,
     ('==', 'be'), None,
     None, ('in', verbsPart),
     ('NONE', 'NONE', 'VERB')],

    ['GR-3-13',
     # Passive, future ('will be V_en')
     ('in', futureMod), None,
     ('==', 'be'), None,
     None, ('in', verbsPart),
     ('FUTURE', 'NONE', 'VERB')],    

    ['GR-3-14',
     # Passive, present progr. ('is being V_en')
     ('in', beFin), ('in', verbsPresent),
     ('==', 'being'), None,
     None, ('in', verbsPart),
     ('PRESENT', 'PROGRESSIVE', 'VERB')],

    ['GR-3-15',
     # Passive, past progr. ('was being V_en')
     ('in', beFin), ('in', verbsPast),
     ('==', 'being'), None,
     None, ('in', verbsPart),
     ('PAST', 'PROGRESSIVE', 'VERB')],

    ['GR-3-16',
     # Passive, infinitive, progr. ('be being V_en')
     ('==', 'be'), ('==', 'VB'),
     ('==', 'being'), None,
     None, ('in', verbsPart),
     ('INFINITIVE', 'PROGRESSIVE', 'VERB')],

    ['GR-3-17',
     # Passive, present perf. ('has been V_en')
     ('in', have),('in', verbsPresent+['VB']),
     ('==', 'been'), None,
     None, ('in', verbsPart),
     ('PRESENT', 'PERFECTIVE', 'VERB')],

    ['GR-3-18',
     # Passive, past perf. ('had been V_en')
     ('in', have),('in', verbsPast),
     ('==', 'been'), None,
     None, ('in', verbsPart),
     ('PAST', 'PERFECTIVE', 'VERB')],

    ['GR-3-19',
     # Passive, infinitive perf. ('(to) have been V_en')
     ('==', 'have'),('==', 'VB'),
     ('==', 'been'), None,
     None, ('in', verbsPart),
     ('INFINITIVE', 'PERFECTIVE', 'VERB')],

    ['GR-3-20',
     # Passive, present participle perfective ('having been V_en')
     ('==', 'having'), None,
     ('==', 'been'), None,
     None, ('==', 'VBN'),
     ('PRESPART', 'PERFECTIVE', 'VERB')]    

    ]


grammarRules4 = [ # Lenght 4 rules

    ['GR-4-1',
     # Active, Aux. "DO" pres., modal "have to" + base form  ('does have to ask')
     ('in', do), ('in', verbsPresent),
     ('==', 'have'), ('==', 'VB'),
     ('==', 'to'), ('==', 'TO'),
     None, ('in', verbsBase),
     ('PPRESENT', 'NONE', 'VERB')],

    ['GR-4-2',
     # Active, Aux. "DO" past, modal "have to" + base form  ('did have to ask')
     ('in', do), ('in', verbsPast),
     ('==', 'have'), ('==', 'VB'), 
     ('==', 'to'), ('==', 'TO'),
     None, ('in', verbsBase),
     ('PAST', 'NONE', 'VERB')],

    ['GR-4-3',
     # Passive, present perfective-progressive ('has been being V_en')
     ('in', have), ('in', verbsPresent+['VB']),
     ('==', 'been'), None,
     ('==', 'being'), None,
     None, ('in', verbsPart),
     ('PRESENT', 'PERFECTIVE_PROGRESSIVE', 'VERB')],

    ['GR-4-4',
     # Passive, past perfective-progressive ('had been being V_en')
     ('in', have), ('in', verbsPresent),
     ('==', 'been'), None,
     ('==', 'being'), None,
     None, ('in', verbsPart),
     ('PAST', 'PERFECTIVE_PROGRESSIVE', 'VERB')],

    ['GR-4-5',
     # Active, pres. fut. "is GOING TO" + base form  ('is going to ask')
     ('in', be), ('in', verbsPresent),
     ('==', 'going'), None,
     ('==', 'to'), ('==', 'TO'),
     None, ('in', verbsBase),
     ('FUTURE', 'NONE', 'VERB')],

    ['GR-4-6',
     # Active, past. fut. "was GOING TO" + base form  ('was going to ask')
     # Loosing information here (PAST component of 'was going to') which
     # should be encoded in "tense", the same attribute as FUTURE
     ('in', be), ('in', verbsPast),
     ('==', 'going'), None,
     ('==', 'to'), ('==', 'TO'),
     None, ('in', verbsBase),
     ('FUTURE', 'NONE', 'VERB')],

    ['GR-4-7',
     # Active, infin., fut. "be GOING TO" + base form  ('be going to ask')
     # Loosing information here (INFINITIVE component of 'be going to') which
     # should be encoded in "tense", the same attribute as FUTURE
     ('==', 'be'), ('==', 'VB'),
     ('==', 'going'), None,
     ('==', 'to'), ('==', 'TO'),
     None, ('in', verbsBase),
     ('FUTURE', 'NONE', 'VERB')],

    ['GR-4-8',
     # Active, pres. progr., modal "HAVE TO" + be V_ing  ('has to be asking')
     ('in', have), ('in', verbsPresent),
     ('==', 'to'), ('==', 'TO'),
     ('==', 'be'), None,
     None, ('==', 'VBG'),
     ('PRESENT', 'PROGRESSIVE', 'VERB')],

    ['GR-4-9',
     # Active, past. progr., modal "HAD TO" + be V_en  ('had to be asking')
     ('in', have), ('in', verbsPast),
     ('==', 'to'), ('==', 'TO'),
     ('==', 'be'), None,
     None, ('==', 'VBG'),
     ('PAST', 'PROGRESSIVE', 'VERB')],

    ['GR-4-10',
     # Active, pres., perf., modal "HAVE TO" + have V_en  ('has to have asked')
     ('in', have), ('in', verbsPresent),
     ('==', 'to'), ('==', 'TO'),
     ('==', 'have'), None,
     None, ('in', verbsPart),
     ('PRESENT', 'PERFECTIVE', 'VERB')],

    ['GR-4-11',
     # Active, past., perf., modal "HAD TO" + have V_en  ('had to have asked')
     ('in', have), ('in', verbsPast),
     ('==', 'to'), ('==', 'TO'),
     ('==', 'have'), None,
     None, ('in', verbsPart),
     ('PAST', 'PERFECTIVE', 'VERB')],

    ['GR-4-12',
     # Passive, pres., modal "HAVE TO" + be V_en  ('has to be asked')
     ('in', have), ('in', verbsPresent),
     ('==', 'to'), ('==', 'TO'),
     ('==', 'be'), None,
     None, ('in', verbsPart),
     ('PRESENT', 'NONE', 'VERB')],

    ['GR-4-13',
     # Passive, past., modal "HAD TO" + be V_en  ('had to be asked')
     ('in', have), ('in', verbsPast),
     ('==', 'to'), ('==', 'TO'),
     ('==', 'be'), None,
     None, ('in', verbsPart),
     ('PAST', 'NONE', 'VERB')],

    ['GR-4-14',
     # Active, pres., perf., modal "HAVE TO" ('has had to eat')
     ('in', have), ('in', verbsPresent),
     ('==', 'had'), None,
     ('==', 'to'), ('==', 'TO'),
     None, ('in', verbsBase),
     ('PRESENT', 'PERFECTIVE', 'VERB')],

    ['GR-4-15',
     # Active, past., perf., modal "HAD TO" ('had had to eat')
     ('in', have), ('in', verbsPast),
     ('==', 'had'), None,
     ('==', 'to'), ('==', 'TO'),
     None, ('in', verbsBase),
     ('PAST', 'PERFECTIVE', 'VERB')],

    ['GR-4-16',
     # Active, infinitive, perf., modal "HAVE TO" ('(to) have had to eat')
     ('==', 'have'), ('==', 'VB'),
     ('==', 'had'), None,
     ('==', 'to'), ('==', 'TO'),
     None, ('in', verbsBase),
     ('INFINITIVE', 'PERFECTIVE', 'VERB')],

    ['GR-4-17',# Active, fut. modal "HAVE TO": ('will have to V')
     ('in', futureMod), None,
     ('==', 'have'), None,
     ('==', 'to'), ('==', 'TO'),
     None, ('in', verbsBase),
     ('FUTURE', 'NONE', 'VERB')],

    ['GR-4-18',
     #  Active, modal + modal "HAVE TO": ('may have to V')
     ('in', allMod), None,
     ('==', 'have'), None,
     ('==', 'to'), ('==', 'TO'),
     None, ('in', verbsBase),    
     ('NONE', 'NONE', 'VERB')],

    ['GR-4-19',
     # Passive, fut. perfective ('will have been V_en')
     ('in', futureMod), None,
     ('==', 'have'), None,
     ('==', 'been'), None,
     None, ('in', verbsPart),
     ('FUTURE', 'PERFECTIVE', 'VERB')],

    ['GR-4-20',
     # Passive, modal perfective ('must have been V_en')
     ('in', allMod), None,
     ('==', 'have'), None,
     ('==', 'been'), None,
     None, ('in', verbsPart),    
    ('NONE', 'PERFECTIVE', 'VERB')],

    ['GR-4-21',
     # Active, fut. perfective-progressive ('will have been V_ing')
     ('in', futureMod), None,
     ('==', 'have'), None,
     ('==', 'been'), None,
     None, ('==', 'VBG'),
     ('FUTURE', 'PERFECTIVE_PROGRESSIVE', 'VERB')],

    ['GR-4-22',
     # Active, modal perfective-progressive ('must have been V_ing')
     ('in', allMod), None,
     ('==', 'have'), None,
     ('==', 'been'), None,
     None, ('==', 'VBG'),
     ('NONE', 'PERFECTIVE_PROGRESSIVE', 'VERB')],

    ['GR-4-23',
     # Passive, fut. progressive ('will be being V_en')
     ('in', futureMod), None,
     ('==', 'be'), None,
     ('==', 'being'), None,
     None, ('in', verbsPart),
     ('FUTURE', 'PROGRESSIVE', 'VERB')],

    ['GR-4-24',
     # Passive, modal progressive ('must be being V_en')
     ('in', allMod), None,
     ('==', 'be'), None,
     ('==', 'being'), None,
     None, ('in', verbsPart),
     ('NONE', 'PROGRESSIVE', 'VERB')],
    
    ]


grammarRules5 = [ # Lenght 5 rules

    ['GR-5-1',
     # Active, pres., perf_progr., modal "HAVE TO" ('has been having to eat')
     ('in', have), ('in', verbsPresent),
     ('==', 'been'), None,
     ('==', 'having'), None,
     ('==', 'to'), ('==', 'TO'),
     None, ('in', verbsBase),
     ('PRESENT', 'PERFECTIVE_PROGRESSIVE', 'VERB')],

    ['GR-5-2',
     # Active, past., perf_progr., modal "HAVE TO" ('had been having to eat')
     ('in', have), ('in', verbsPast),
     ('==', 'been'), None,
     ('==', 'having'), None,
     ('==', 'to'), ('==', 'TO'),
     None, ('in', verbsBase),
     ('PAST', 'PERFECTIVE_PROGRESSIVE', 'VERB')],

    ['GR-5-3',
     # Active, infin., perf_progr., modal "HAVE TO" ('(to) have been having to eat')
     ('==', 'have'), ('==', 'VB'),
     ('==', 'been'), None,
     ('==', 'having'), None,
     ('==', 'to'), ('==', 'TO'),
     None, ('in', verbsBase),
     ('INFINITIVE', 'PERFECTIVE_PROGRESSIVE', 'VERB')],

    ['GR-5-4',
     # Active, pres. progr., modal "HAVE TO" + be V_ing  ('does have to be asking')
     ('in', do), ('in', verbsPresent),
     ('==', 'have'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'be'), None,
     None, ('==', 'VBG'),
     ('PRESENT', 'PROGRESSIVE', 'VERB')],

    ['GR-5-5',
     # Active, past. progr., modal "HAD TO" + be V_en  ('did have to be asking')
     ('in', do), ('in', verbsPast),
     ('==', 'have'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'be'), None,
     None, ('==', 'VBG'),
     ('PAST', 'PROGRESSIVE', 'VERB')],

    ['GR-5-6',
     # Active, pres., perf., modal "HAVE TO" + have V_en  ('does have to have asked')
     ('in', do), ('in', verbsPresent),
     ('==', 'have'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'have'), None,
     None, ('in', verbsPart),
     ('PRESENT', 'PERFECTIVE', 'VERB')],

    ['GR-5-7',
     # Active, past., perf., modal "HAD TO" + have V_en  ('did have to have asked')
     ('in', do), ('in', verbsPast),
     ('==', 'have'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'have'), None,
     None, ('in', verbsPart),
     ('PAST', 'PERFECTIVE', 'VERB')],

    ['GR-5-8',
     # Passive, pres., modal "HAVE TO" + be V_en  ('does have to be asked')
     ('in', do), ('in', verbsPresent),
     ('==', 'have'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'be'), None,
     None, ('in', verbsPart),
     ('PRESENT', 'NONE', 'VERB')],

    ['GR-5-9',
     # Passive, past., modal "HAD TO" + be V_en  ('did have to be asked')
     ('in', do), ('in', verbsPast),
     ('==', 'have'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'be'), None,
     None, ('in', verbsPart),
     ('PAST', 'NONE', 'VERB')],

    ['GR-5-10',
     # Active, pres., perf_progr., modal "HAVE TO" + have been V_ing  ('has to have been asking')
     ('in', have), ('in', verbsPresent),
     ('==', 'to'), ('==', 'TO'),
     ('==', 'have'), None,
     ('==', 'been'), None,
     None, ('==', 'VBG'),
     ('PRESENT', 'PERFECTIVE_PROGRESSIVE', 'VERB')],

    ['GR-5-11',
     # Active, past., perf_progr., modal "HAD TO" + have been V_ing ('had to have been asking')
     ('in', have), ('in', verbsPast),
     ('==', 'to'), ('==', 'TO'),
     ('==', 'have'), None,
     ('==', 'been'), None,
     None, ('==', 'VBG'),
     ('PAST', 'PERFECTIVE_PROGRESSIVE', 'VERB')],

    ['GR-5-12',
     # Passive, pres., perf., modal "HAVE TO" + have been V_en  ('has to have been asked')
     ('in', have), ('in', verbsPresent),
     ('==', 'to'), ('==', 'TO'),
     ('==', 'have'), None,
     ('==', 'been'), None,
     None, ('in', verbsPart),
     ('PRESENT', 'PERFECTIVE', 'VERB')],

    ['GR-5-13',
     # Passive, past., perf., modal "HAD TO" + have been V_en ('had to have been asked')
     ('in', have), ('in', verbsPast),
     ('==', 'to'), ('==', 'TO'),
     ('==', 'have'), None,
     ('==', 'been'), None,
     None, ('in', verbsPart),
     ('PAST', 'PERFECTIVE', 'VERB')],

    ['GR-5-14',
     # Passive, pres., progr., modal "HAVE TO" + be being V_en  ('has to be being asked')
     ('in', have), ('in', verbsPresent),
     ('==', 'to'), ('==', 'TO'),
     ('==', 'be'), None,
     ('==', 'being'), None,
     None, ('in', verbsPart),
     ('PRESENT', 'PROGRESSIVE', 'VERB')],

    ['GR-5-15',
     # Passive, past., progr., modal "HAD TO" + be being V_en ('had to be being asked')
     ('in', have), ('in', verbsPast),
     ('==', 'to'), ('==', 'TO'),
     ('==', 'be'), None,
     ('==', 'being'), None,
     None, ('in', verbsPart),
     ('PAST', 'PROGRESSIVE', 'VERB')],

    ['GR-5-16',
     # Active, progr., pres. fut. "is GOING TO"  ('is going to be asking')
     ('in', be), ('in', verbsPresent),
     ('==', 'going'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'be'), None,
     None, ('==', 'VBG'),
     ('FUTURE', 'PROGRESSIVE', 'VERB')],

    ['GR-5-17',
     # Active, progr., past. fut. "was GOING TO"  ('was going to be eating')
     # Loosing information here (PAST component of 'was going to') which
     # should be encoded in "tense", the same attribute as FUTURE
     ('in', be), ('in', verbsPast),
     ('==', 'going'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'be'), None,
     None, ('==', 'VBG'),
     ('FUTURE', 'PROGRESSIVE', 'VERB')],

    ['GR-5-18',
     # Active, progr., infin., fut. "be GOING TO"  ('be going to be eating')
     # Loosing information here (INFINITIVE component of 'be going to') which
     # should be encoded in "tense", the same attribute as FUTURE
     ('==', 'be'), ('==', 'VB'),
     ('==', 'going'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'be'), None,
     None, ('==', 'VBG'),
     ('FUTURE', 'PROGRESSIVE', 'VERB')],

    ['GR-5-19',
     # Active, perf., pres. fut. "is GOING TO"  ('is going to have asked')
     ('in', be), ('in', verbsPresent),
     ('==', 'going'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'have'), None,
     None, ('in', verbsPart),
     ('FUTURE', 'PERFECTIVE', 'VERB')],

    ['GR-5-20',
     # Active, perf., past. fut. "was GOING TO"  ('was going to have asked')
     # Loosing information here (PAST component of 'was going to') which
     # should be encoded in "tense", the same attribute as FUTURE
     ('in', be), ('in', verbsPast),
     ('==', 'going'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'have'), None,
     None, ('in', verbsPart),
     ('FUTURE', 'PERFECTIVE', 'VERB')],

    ['GR-5-21',
     # Active, perf., infin., fut. "be GOING TO"  ('be going to have asked')
     # Loosing information here (INFINITIVE component of 'be going to') which
     # should be encoded in "tense", the same attribute as FUTURE
     ('==', 'be'), ('==', 'VB'),
     ('==', 'going'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'have'), None,
     None, ('in', verbsPart),
     ('FUTURE', 'PERFECTIVE', 'VERB')],

    ['GR-5-22',
     # Passive, pres. fut. "is GOING TO"  ('is going to be asked')
     ('in', be), ('in', verbsPresent),
     ('==', 'going'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'be'), None,
     None, ('in', verbsPart),
     ('FUTURE', 'NONE', 'VERB')],

    ['GR-5-23',
     # Passive, past. fut. "was GOING TO"  ('was going to be eaten')
     # Loosing information here (PAST component of 'was going to') which
     # should be encoded in "tense", the same attribute as FUTURE
     ('in', be), ('in', verbsPast),
     ('==', 'going'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'be'), None,
     None, ('in', verbsPart),
     ('FUTURE', 'NONE', 'VERB')],

    ['GR-5-24',
     # Passive, infin., fut. "be GOING TO"  ('be going to be eaten')
     # Loosing information here (INFINITIVE component of 'be going to') which
     # should be encoded in "tense", the same attribute as FUTURE
     ('==', 'be'), ('==', 'VB'),
     ('==', 'going'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'be'), None,
     None, ('in', verbsPart),
     ('FUTURE', 'NONE', 'VERB')],

    ['GR-5-25',
     # Active, perf., fut. modal "HAVE TO": ('will have had to V')
     ('in', futureMod), None,
     ('==', 'have'), None,
     ('==', 'had'), None,
     ('==', 'to'), ('==', 'TO'),
     None, ('in', verbsPart),
     ('FUTURE', 'PERFECTIVE', 'VERB')],

    ['GR-5-26',
     #  Active, perf., modal + modal "HAVE TO": ('may have had to V')
     ('in', allMod), None,
     ('==', 'have'), None,
     ('==', 'had'), None,
     ('==', 'to'), ('==', 'TO'),
     None, ('in', verbsPart),    
     ('NONE', 'PERFECTIVE', 'VERB')],

    ['GR-5-27',
     # Active, perf, fut., modal "HAVE TO": ('will have to have V_en')
     ('in', futureMod), None,
     ('==', 'have'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'have'), None,
     None, ('in', verbsBase),
     ('FUTURE', 'PERFECTIVE', 'VERB')],

    ['GR-5-28',
     #  Active, perf, modal + modal "HAVE TO": ('may have to have V_en')
     ('in', allMod), None,
     ('==', 'have'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'have'), None,
     None, ('in', verbsBase),    
     ('NONE', 'PERFECTIVE', 'VERB')],

    ['GR-5-29',
     # Active, prog., fut., modal "HAVE TO": ('will have to be V_ing')
     ('in', futureMod), None,
     ('==', 'have'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'be'), None,
     None, ('==', 'VBG'),
     ('FUTURE', 'PROGRESSIVE', 'VERB')],

    ['GR-5-30',
     #  Active, prog., modal + modal "HAVE TO": ('may have to be V_ing')
     ('in', allMod), None,
     ('==', 'have'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'be'), None,
     None, ('==', 'VBG'),
     ('NONE', 'PROGRESSIVE', 'VERB')],

    ['GR-5-31',
     # Passive, fut., modal "HAVE TO": ('will have to be V_en')
     ('in', futureMod), None,
     ('==', 'have'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'be'), None,
     None, ('in', verbsPart),
     ('FUTURE', 'NONE', 'VERB')],

    ['GR-5-32',
     #  Passive, modal + modal "HAVE TO": ('may have to be V_en')
     ('in', allMod), None,
     ('==', 'have'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'be'), None,
     None, ('in', verbsPart),
     ('NONE', 'NONE', 'VERB')],

    ['GR-5-33',# Active, fut., "will be going to"   ('will be going to ask')
     ('in', futureMod), None,
     ('==', 'be'), None,
     ('==', 'going'), None,
     ('==', 'to'), ('==', 'TO'),
     None, ('in', verbsBase),
     ('FUTURE', 'NONE', 'VERB')],

    ['GR-5-34',
     # Active, fut. modal "may be going to ask" ('may be going to ask')
     ('in', allMod), None,
     ('==', 'be'), None,
     ('==', 'going'), None,
     ('==', 'to'), ('==', 'TO'),
     None, ('in', verbsBase),
     ('FUTURE', 'NONE', 'VERB')],

    ['GR-5-35',
     # Active, fut. progr., modal "will have to" + be V_ing  ('will have to be asking')
     ('in', futureMod), None,
     ('==', 'have'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'be'), None,
     None, ('==', 'VBN'),
     ('FUTURE', 'PROGRESSIVE', 'VERB')],

    ['GR-5-36',
     # Passive, fut. modal "will have to be" + V_en  ('will have to be asked')
     ('in', futureMod), None,
     ('==', have), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'be'), None,
     None, ('in', verbsPart),
     ('FUTURE', 'NONE', 'VERB')],

    ['GR-5-37',
     # Active, progr., modal "may + have to" + be V_ing  ('may have to be asking')
     ('in', futureMod), None,
     ('==', 'have'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'be'), None,
     None, ('==', 'VBN'),
     ('NONE', 'PROGRESSIVE', 'VERB')],

    ['GR-5-38',
     # Passive, modal "may + have to be" + V_en  ('may have to be asked')
     ('in', futureMod), None,
     ('==', have), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'be'), None,
     None, ('in', verbsPart),
     ('NONE', 'NONE', 'VERB')],

    ['GR-5-39',
     # Passive, fut. perf_progr. ('will have been being asked')
     ('in', futureMod), None,
     ('==', 'have'), None,
     ('==', 'been'), None,
     ('==', 'being'), None,
     None, ('in', verbsPart),
     ('FUTURE', 'PERFECTIVE_PROGRESSIVE', 'VERB')],

    ['GR-5-40',
     # Passive, modal  perf_progr. ('may have been being asked')
     ('in', allMod), None,
     ('==', 'have'), None,
     ('==', 'been'), None,
     ('==', 'being'), None,
     None, ('in', verbsPart),
     ('NONE', 'PERFECTIVE_PROGRESSIVE', 'VERB')]

    ]


grammarRules6 = [ # Lenght 6 rules

    ['GR-6-1',
     # Active, pres., perf_progr., modal "HAVE TO" + have been V_ing  ('does have to have been asking')
     ('in', do), ('in', verbsPresent),
     ('==', 'have'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'have'), None,
     ('==', 'been'), None,
     None, ('==', 'VBG'),
     ('PRESENT', 'PERFECTIVE_PROGRESSIVE', 'VERB')],

    ['GR-6-2',
     # Active, past., perf_progr., modal "HAD TO" + have been V_ing ('did have to have been asking')
     ('in', do), ('in', verbsPast),
     ('==', 'have'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'have'), None,
     ('==', 'been'), None,
     None, ('==', 'VBG'),
     ('PAST', 'PERFECTIVE_PROGRESSIVE', 'VERB')],

    ['GR-6-3',
     # Passive, pres., perf., modal "HAVE TO" + have been V_en  ('does have to have been asked')
     ('in', do), ('in', verbsPresent),
     ('==', 'have'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'have'), None,
     ('==', 'been'), None,
     None, ('in', verbsPart),
     ('PRESENT', 'PERFECTIVE', 'VERB')],

    ['GR-6-4',
     # Passive, past., perf., modal "HAD TO" + have been V_en ('did have to have been asked')
     ('in', do), ('in', verbsPast),
     ('==', 'have'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'have'), None,
     ('==', 'been'), None,
     None, ('in', verbsPart),
     ('PAST', 'PERFECTIVE', 'VERB')],

    ['GR-6-5',
     # Passive, pres., progr., modal "HAVE TO" + be being V_en  ('does have to be being asked')
     ('in', do), ('in', verbsPresent),
     ('==', 'have'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'be'), None,
     ('==', 'being'), None,
     None, ('in', verbsPart),
     ('PRESENT', 'PROGRESSIVE', 'VERB')],

    ['GR-6-6',
     # Passive, past., progr., modal "HAD TO" + be being V_en ('did have to be being asked')
     ('in', do), ('in', verbsPast),
     ('==', 'have'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'be'), None,
     ('==', 'being'), None,
     None, ('in', verbsPart),
     ('PAST', 'PROGRESSIVE', 'VERB')],

    ['GR-6-7',
     # Active, pres. fut., perf_progr., "is going to have been V_ing"
     ('in', be), ('in', verbsPresent),
     ('==', 'going'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'have'), None,
     ('==', 'been'), None,
     None, ('==', 'VBG'),
     ('FUTURE', 'PERFECTIVE_PROGRESSIVE', 'VERB')],

    ['GR-6-8',
     # Active, past fut., perf_progr., "was going to have been V_ing"
     # Loosing information here (PAST component of 'was going to') which
     # should be encoded in "tense", the same attribute as FUTURE
     ('in', be), ('in', verbsPast),
     ('==', 'going'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'have'), None,
     ('==', 'been'), None,
     None, ('==', 'VBG'),
     ('FUTURE', 'PERFECTIVE_PROGRESSIVE', 'VERB')],

    ['GR-6-9',
     # Active, infin., fut., perf_progr., "BE going to have been V_ing"
     # Loosing information here (INFINITIVE component of 'be going to') which
     # should be encoded in "tense", the same attribute as FUTURE
     ('in', be), ('==', 'VB'),
     ('==', 'going'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'have'), None,
     ('==', 'been'), None,
     None, ('==', 'VBG'),
     ('FUTURE', 'PERFECTIVE_PROGRESSIVE', 'VERB')],

    ['GR-6-10',
     # Active, pres. fut., modal "HAVE TO":  "is going to have to V"
     ('in', be), ('in', verbsPresent),        
     ('==', 'going'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'have'), None,
     ('==', 'to'), ('==', 'TO'),
     None, ('in', verbsBase),
     ('FUTURE', 'NONE', 'VERB')],

    ['GR-6-11',
     # Active, past fut., modal "HAVE TO":  "was going to have to V"
     # Loosing information here (PAST component of 'was going to') which
     # should be encoded in "tense", the same attribute as FUTURE
     ('in', be), ('in', verbsPast),
     ('==', 'going'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'have'), None,
     None, ('in', verbsBase),
     ('FUTURE', 'NONE', 'VERB')],

    ['GR-6-12',
     # Active, infin. fut., modal "HAVE TO":  "(to) be going to have to V"
     # Loosing information here (INFINITIVE component of 'be going to') which
     # should be encoded in "tense", the same attribute as FUTURE
     ('in', be), ('==', 'VB'),
     ('==', 'going'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'have'), None,
     ('==', 'to'), ('==', 'TO'),
     None, ('in', verbsBase),
     ('FUTURE', 'NONE', 'VERB')],

    ['GR-6-13',
     # Passive, pres. fut., perf., "is going to have been V_en"
     ('in', be), ('in', verbsPresent),
     ('==', 'going'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'have'), None,
     ('==', 'been'), None,
     None, ('in', verbsPart),
     ('FUTURE', 'PERFECTIVE', 'VERB')],

    ['GR-6-14',
     # Passive, past fut., perf., "was going to have been V_en"
     # Loosing information here (PAST component of 'was going to') which
     # should be encoded in "tense", the same attribute as FUTURE
     ('in', be), ('in', verbsPast),
     ('==', 'going'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'have'), None,
     ('==', 'been'), None,
     None, ('in', verbsPart),
     ('FUTURE', 'PERFECTIVE', 'VERB')],

    ['GR-6-15',
     # Passive, infin., fut., perf., "BE going to have been V_en"
     # Loosing information here (INFINITIVE component of 'be going to') which
     # should be encoded in "tense", the same attribute as FUTURE
     ('in', be), ('==', 'VB'),
     ('==', 'going'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'have'), None,
     ('==', 'been'), None,
     None, ('in', verbsPart),
     ('FUTURE', 'PERFECTIVE', 'VERB')],

    ['GR-6-16',
     # Active, perf, fut., modal "HAVE TO": ('will have had to have V_en')
     ('in', futureMod), None,
     ('==', 'have'), None,
     ('==', 'had'), None, 
     ('==', 'to'), ('==', 'TO'),
     ('==', 'have'), None,
     None, ('in', verbsBase),
     ('FUTURE', 'PERFECTIVE', 'VERB')],

    ['GR-6-17',
     #  Active, perf, modal + modal "HAVE TO": ('may have had to have V_en')
     ('in', allMod), None,
     ('==', 'have'), None,
     ('==', 'had'), None, 
     ('==', 'to'), ('==', 'TO'),
     ('==', 'have'), None,
     None, ('in', verbsBase),    
    ('NONE', 'PERFECTIVE', 'VERB')],

    ['GR-6-18',
     # Active,perf_ prog., fut., modal "HAVE TO": ('will have had to be V_ing')
     # is ASPECT correct? 
     ('in', futureMod), None,
     ('==', 'have'), None,
     ('==', 'had'), None, 
     ('==', 'to'), ('==', 'TO'),
     ('==', 'be'), None,
     None, ('==', 'VBG'),
     ('FUTURE', 'PERFECTIVE_PROGRESSIVE', 'VERB')],

    ['GR-6-19',
     #  Active, perf_prog., modal + modal "HAVE TO": ('may have had to be V_ing')
     # is ASPECT correct?
     ('in', allMod), None,
     ('==', 'have'), None,
     ('==', 'had'), None, 
     ('==', 'to'), ('==', 'TO'),
     ('==', 'be'), None,
     None, ('==', 'VBG'),
    ('NONE', 'PERFECTIVE_PROGRESSIVE', 'VERB')],

    ['GR-6-20',
     # Passive, perf, fut., modal "HAVE TO": ('will have had to be V_en')
     ('in', futureMod), None,
     ('==', 'have'), None,
     ('==', 'had'), None, 
     ('==', 'to'), ('==', 'TO'),
     ('==', 'be'), None,
     None, ('in', verbsPart),
     ('FUTURE', 'PERFECTIVE', 'VERB')],

    ['GR-6-21',
     #  Passive, perf, modal + modal "HAVE TO": ('may have had to be V_en')
     ('in', allMod), None,
     ('==', 'have'), None,
     ('==', 'had'), None, 
     ('==', 'to'), ('==', 'TO'),
     ('==', 'be'), None,
     None, ('in', verbsPart),
     ('NONE', 'PERFECTIVE', 'VERB')],

    ['GR-6-22',
     # Active, perf., fut., "will be going to have V_en" ('will be going to have asked')
     ('in', futureMod), None,
     ('==', 'be'), None,
     ('==', 'going'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'have'), None,
     None, ('in', verbsPart),
     ('FUTURE', 'PERFECTIVE', 'VERB')],

    ['GR-6-23',
     # Active, perf., modal "may be going to have V_en" ('may be going to have asked')
     ('in', allMod), None,
     ('==', 'be'), None,
     ('==', 'going'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'have'), None,
     None, ('in', verbsPart),
     ('FUTURE', 'PERFECTIVE', 'VERB')],

    ['GR-6-24',
     # Active, progr., fut., "will be going to be V_ing" ('will be going to be asking')
     ('in', futureMod), None,
     ('==', 'be'), None,
     ('==', 'going'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'be'), None,
     None, ('==', 'VBG'),
     ('FUTURE', 'PROGRESSIVE', 'VERB')],

    ['GR-6-25',
     # Active, progr., fut., modal "may be going to be V_ing" ('may be going to be asking')
     ('in', allMod), None,
     ('==', 'be'), None,
     ('==', 'going'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'be'), None,
     None, ('==', 'VBG'),
     ('FUTURE', 'PROGRESSIVE', 'VERB')],

    ['GR-6-26',
     # Passive, fut., "will be going to be V_en" ('will be going to be asked')
     ('in', futureMod), None,
     ('==', 'be'), None,
     ('==', 'going'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'be'), None,
     None, ('in', verbsPart),
     ('FUTURE', 'NONE', 'VERB')],

    ['GR-6-27',
     # Passive, fut., modal "may be going to be V_en" ('may be going to be asked')
     ('in', allMod), None,
     ('==', 'be'), None,
     ('==', 'going'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'be'), None,
     None, ('in', verbsPart),
     ('FUTURE', 'NONE', 'VERB')],

    ]


grammarRules7 = [ # Lenght 7 rules:

    ['GR-7-1',
     # Active, fut., modal + modal "HAVE TO":  "may be going to have to V"
     ('in', allMod), None, 
     ('in', be), ('in', verbsPresent),        
     ('==', 'going'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'have'), None,
     ('==', 'to'), ('==', 'TO'),
     None, ('in', verbsBase),
     ('FUTURE', 'NONE', 'VERB')],

    ['GR-7-2',
     # Active, fut., modal future + modal "HAVE TO":  "will be going to have to V"
     ('in', futureMod), None,
     ('in', be), ('in', verbsPast),           
     ('==', 'going'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'have'), None,
     None, ('in', verbsBase),
     ('FUTURE', 'NONE', 'VERB')],

    ['GR-7-3',
     # Active, perf_progr., fut., "will be going to have been V_ing" ('will be going to have been asking')
     ('in', futureMod), None,
     ('==', 'be'), None,
     ('==', 'going'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'have'), None,
     ('==', 'been'), None,
     None, ('==', 'VBG'),
     ('FUTURE', 'PERFECTIVE_PROGRESSIVE', 'VERB')],

    ['GR-7-4',
     # Active, perf_progr.,fut.  modal, "may be going to have been V_ing" ('may be going to have been asking')
     ('in', allMod), None,
     ('==', 'be'), None,
     ('==', 'going'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'have'), None,
     ('==', 'been'), None,     
     None, ('==', 'VBG'),
     ('FUTURE', 'PERFECTIVE_PROGRESSIVE', 'VERB')],

    ['GR-7-5',
     # Passive, perf., fut., "will be going to have been V_en" ('will be going to have been asked')
     ('in', futureMod), None,
     ('==', 'be'), None,
     ('==', 'going'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'have'), None,
     ('==', 'been'), None,
     None, ('in', verbsPart),
     ('FUTURE', 'PERFECTIVE', 'VERB')],

    ['GR-7-6',
     # Passive, perf., fut. modal, "may be going to have been V_en" ('may be going to have been asked')
     ('in', allMod), None,
     ('==', 'be'), None,
     ('==', 'going'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'have'), None,
     ('==', 'been'), None,     
     None, ('in', verbsPart),
     ('FUTURE', 'PERFECTIVE', 'VERB')],

    ['GR-7-7',
     # Passive, progr., fut., "will be going to be being V_en" ('will be going to be being asked')
     ('in', futureMod), None,
     ('==', 'be'), None,
     ('==', 'going'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'be'), None,
     ('==', 'being'), None,
     None, ('in', verbsPart),
     ('FUTURE', 'PROGRESSIVE', 'VERB')],

    ['GR-7-8',
     # Passive, progr., fut. modal, "may be going to be being V_en" ('may be going to be being asked')
     ('in', allMod), None,
     ('==', 'be'), None,
     ('==', 'going'), None,
     ('==', 'to'), ('==', 'TO'),
     ('==', 'be'), None,
     ('==', 'being'), None,
     None, ('in', verbsPart),
     ('FUTURE', 'PROGRESSIVE', 'VERB')],        

    ]


FEATURE_RULES = { 1: grammarRules1,
                  2: grammarRules2,
                  3: grammarRules3,
                  4: grammarRules4,
                  5: grammarRules5,
                  6: grammarRules6,
                  7: grammarRules7 }
