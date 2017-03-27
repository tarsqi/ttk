"""test_cases_slink.py

Set of test cases for Slinks and Alinks. These tests are not intended to be a
thorough coverage test, but they try to hit enough cases so that errors are
likely to be found.

Cases are split into a SIMPLE category with some quick and dirty minimal checks
and sets of cases for each relation type. The relation type cases were initially
all taken from Timebank as processed by TTK on December 2015. These cases were
manually selected from the output of testing/create_slinket_cases.py.

Cases added later should have comments.

Each case always has six fields:

1- relation type
2- file name where the relation occurred (can be None)
3- FSA rule used (None if not tested)
4- character offsets of first event
5- character offsets of second event (the subordinated event)
6- a sentence

There is an optional seventh field which can be used to determine whether there
should or should not be an SLINK spanning the two events. Setting it to False
tests for the absence of an slink.

"""


SIMPLE = [

    ('EVIDENTIAL', None, None, (5, 8), (20, 25), "John saw the miners build a fence."),

    ('EVIDENTIAL', None, None, (3, 7), (17, 22), "He said the dogs slept."),

    ('MODAL', None, None, (3, 9), (13, 17), "He wanted to walk."),

    ('MODAL', None, None, (3, 9), (13, 17), "He xanted to walk.", False),

    # this should not raise an error, which happens if there are two move events
    ('DUMMY', None, None, (0, 0), (0, 0), "All Arabs would have to move behind Iraq.", False)
]


ALINKS = [

    ('CONTINUES', None, None, (5, 14), (18, 22), "They continued to walk.")
]


COUNTER_FACTIVE = [

    ('COUNTER_FACTIVE', 'AP900815-0044.xml', 'toClause1', (39, 47), (51, 58),
     "In an interview from Jordan on ABC, he declined to discuss details, but said:" +
     " ``I don't think that his majesty would be traveling at this crucial moment if" +
     " the Iraqi leadership did not have a rational approach to the future.''"),

    ('COUNTER_FACTIVE', 'AP900815-0044.xml', 'NP_event1', (67, 72), (79, 84),
     "The United States has provided most of the naval vessels so far to block" +
     " Iraqi trade, with Britain, West Germany and Australia among the other nations" +
     " lending support at sea."),

    ('COUNTER_FACTIVE', 'APW19980227.0476.xml', 'NP_event1', (128, 135), (140, 145),
     "THE HAGUE, Netherlands (AP) _ The World Court Friday rejected U.S. and" +
     " British objections to a Libyan World Court case that has blocked the trial" +
     " of two Libyans suspected of blowing up a Pan Am jumbo jet over Scotland in 1988."),

    ('COUNTER_FACTIVE', 'APW19980227.0487.xml', 'toClause1', (65, 71), (75, 81),
     "Margalit Har-Shefi, 22, has pleaded innocent to charges that she failed to report" +
     " Yigal Amir's plan to kill Rabin."),

    ('COUNTER_FACTIVE', 'wsj_0106.xml', 'toClause1', (3, 11), (15, 22),
     "He declined to discuss other terms of the issue."),

    ('COUNTER_FACTIVE', 'wsj_0173.xml', 'toClause1', (30, 36), (40, 44),
     "But as the craze died, Coleco failed to come up with another winner and filed for" +
     " bankruptcy-law protection in July 1988."),

    # ('COUNTER_FACTIVE', 'wsj_0471.xml', 'NP_event1', (131, 138), (142, 149),
    # "DPC, an investor group led by New York-based Crescott Investment Associates, had" +
    # " itself filed a suit in state court in Los Angeles seeking to nullify the agreement.")
]


EVIDENTIAL = [

    ('EVIDENTIAL', 'AP900815-0044.xml', 'thatClause_NOT_that', (22, 26), (72, 79),
     "Soviet officials also said Soviet women," +
     " children and invalids would be allowed to leave Iraq."),

    ('EVIDENTIAL', 'AP900815-0044.xml', 'thatClause_NOT_that', (7, 11), (15, 21),
     "Saddam said he sought to ``turn the gulf into a lake of peace free of foreign fleets" +
     " and forces that harbor ill intentions against us.''"),

    ('EVIDENTIAL', 'AP900815-0044.xml', 'thatClause_that', (5, 9), (86, 94),
     "Bush told a news conference on Tuesday that the naval barricade now in force" +
     " might be extended to Jordan's Aqaba ``if it is a hole through which commerce flows''" +
     " in and out of Iraq."),

    ('EVIDENTIAL', 'APW19980213.1380.xml', 'thatClause_that', (7, 16), (38, 43),
     "Police confirmed Friday that the body found along a highway in this municipality" +
     " 15 miles south of San Juan belonged to Jorge Hernandez, 49."),

    ('EVIDENTIAL', 'APW19980227.0494.xml', 'thatClause_NOT_that', (11, 15), (46, 52),
     "Kuchma has said repeatedly that Ukraine would remain neutral for the foreseeable future."),

    ('EVIDENTIAL', 'APW19980227.0494.xml', 'thatClause_that', (30, 37), (55, 66),
     "In the past, Russia has often claimed that Ukraine was undermining efforts" +
     " at closer cooperation within the CIS.")
]


FACTIVE = [

    ('FACTIVE', 'APW19980213.1310.xml', 'NP_event1', (131, 139), (144, 150),
     "Former prime minister Paul Keating, who put the republic issue in the spotlight in his" +
     " unsuccessful 1996 campaign for re-election, welcomed the result."),

    ('FACTIVE', 'APW19980213.1320.xml', 'NP_event1', (69, 76), (83, 90),
     "Thomson, in India to talk to tourism leaders, said the flights would provide" +
     " extra support to the growing tourism market."),

    ('FACTIVE', 'APW19980213.1380.xml', 'thatClause_NOT_that', (108, 113), (164, 171),
     "CAGUAS, Puerto Rico (AP) _ Kidnappers kept their promise to kill a store owner" +
     " they took hostage and police found the man's dismembered and decapitated body Friday" +
     " wrapped in plastic garbage bags."),

    ('FACTIVE', 'APW19980227.0487.xml', 'thatClause_that', (10, 22), (91, 97),
     "Har-Shefi acknowledged she told police interrogators that Rabin was a traitor" +
     " and that she prayed for him to have a heart attack and die."),

    ('FACTIVE', 'APW19980227.0489.xml', 'indirectInterrog', (109, 120), (125, 129),
     "Foreign ministers of member-states meeting in the Ethiopian capital agreed to set up" +
     " a seven-member panel to investigate who shot down Rwandan President Juvenal Habyarimana's" +
     " plane on April 6, 1994.")
]


MODAL = [

    ('MODAL', 'ABC19980108.1830.0711.xml', 'toClause1', (51, 55), (59, 62),
     "So for Hong Kong, it's time, as investment bankers like to say, to reposition."),

    ('MODAL', 'AP900815-0044.xml', 'toClause1', (32, 40), (47, 56),
     "At least 50,000 U.S. troops are expected to be committed to Desert Shield within weeks," +
     " including Marines, Army air assault forces, paratroopers and infantry."),

    ('MODAL', 'APW19980213.1310.xml', 'NP_event1', (2, 6), (9, 19),
     "I want a referendum,'' Howard said."),

    ('MODAL', 'APW19980213.1380.xml', 'toClause3', (11, 17), (28, 34),
     "A passerby called police to report the body alongside the road.")
]


NEG_EVIDENTIAL = [

    ('NEG_EVIDENTIAL', 'APW19980227.0487.xml', 'NP_event1', (9, 15), (16, 27),
     "She also denied accusations made by Amir's brother, Hagai, that she joined" +
     " an anti-Arab underground movement.")
]

NOT_USED = [
    # not used because it fails event though it shouldn't, find out why
    # the double quotes may be an issue
    ('NEG_EVIDENTIAL', 'wsj_0026.xml', 'NP_event1', (87,93), (104,113),
     "The White House said Mr. Bush decided to grant duty-free status for 18 categories," +
     " but turned down such treatment for other types of watches \"because of the potential" +
     " for material injury to watch producers located in the U.S. and the Virgin Islands.\""),

    # not used because it fails event though it shouldn't, find out why
    ('NEG_EVIDENTIAL', 'wsj_0778.xml', 'NP_event1', (111,120), (124,128),
     "They also worry that if the government applies asset-forfeiture laws broadly," +
     " the best defense lawyers will be unwilling to take criminal cases unless they" +
     " are assured of being paid."),

    # not used because it fails event though it shouldn't, find out why
    ('NEG_EVIDENTIAL', 'wsj_1006.xml', 'thatClause_that', (30,36), (102,106),
     "Mr. Nadeau said he intends to remain Provigo's chief executive only until the" +
     " non-food businesses are sold, after a which a new chief executive will be named.")
]


ALINK_TESTS = ALINKS
SLINK_TESTS = SIMPLE + COUNTER_FACTIVE + EVIDENTIAL + FACTIVE + MODAL + NEG_EVIDENTIAL
