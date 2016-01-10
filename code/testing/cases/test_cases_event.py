"""test_cases_event.py

Event test cases have at least 4 elements:

1. the name of the test
2. the sentence
3. begin offset of the event
4. end offset of the event

These cases test for the presence of an EVENT tag in the Tarsqi output. To test
for the absence of an event, simply add None as a fifth element.

You can also test for particular values of attributes. Simply add pairs of
attribute name and attribute value as extra elements after the fourth element.

Note that you cannot add None as a fifth element and then add attribute-value
pairs in later elements.

"""


EVENT_TESTS = [
    ('NOUN-1', "The war is over.", 4, 7, ('class', 'OCCURRENCE'), ('tense', 'NONE')),
    ('NOUN-2', "The man is old.", 4, 7, None),
    ('VERB-1', "Fido barks.", 5, 10),
    ('VERB-2', "John sleeps today.", 5, 11),
    # need case for MODAL
    ('BE-ADJ-1', "The door is open.", 12, 16),
    ('BE-NOM-1', "There was a war.", 12, 15),
    ('BE-NOM-2', "There was a war.", 6, 9, None),
    ('BE-NOM-3', "There was a man.", 6, 9, None),
    ('BE-NOM-4', "There was a man.", 12, 15, None),
    ('BECOME-1', "Women have become the sole support of their families.", 11, 17),
    ('BECOME-ADJ-1', "Women have become alarmed.", 11, 17),
    ('BECOME-ADJ-2', "Women have become alarmed.", 18, 25),
    ('CONTINUE-1', "The earnings continued to be excellent.", 13, 22),
    ('CONTINUE-ADJ-1', "The earnings continued to be excellent.", 13, 22),
    ('CONTINUE-ADJ-2', "The economic embargo on materials continued unabated.", 34, 43),
    ('CONTINUE-ADJ-3', "The economic embargo on materials continued unabated.", 44, 52),
    ('DO-1', "You can do that.", 8, 10),
    # need case for DO-AUX
    ('GOING-1', "The fundamental change the industry is going through.", 39, 44),
    ('GOING-TO-1', "We are going to maintain our forces in the region.", 7, 12, None),
    ('GOING-TO-2', "We are going to maintain our forces in the region.", 16, 24), # FUTURE
    ('HAVE-1-1', "All Arabs would have to move behind Iraq.", 16, 20, None),
    ('HAVE-1-2', "All Arabs would have to move behind Iraq.", 24, 28),
    ('HAVE-2-1', "The Iraqi leadership did not have a rational approach.", 29, 33),
    ('KEEP-1', "The stocks they keep on hand to sell investors.", 16, 20), # ASPECTUAL
    ('KEEP-2', "They intend to keep interest rates unchanged.", 15, 19), # ASPECTUAL
    ('KEEP-3', "They intend to keep interest rates unchanged.", 35, 44), # STATE
]
