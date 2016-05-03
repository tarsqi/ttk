"""test_cases_timex.py

GUTime test cases have at least 4 elements:

1. the name of the test
2. the sentence
3. begin offset of the time expression
4. end offset of the time expression

These cases test for the presence of an TIMEX3 tag in the Tarsqi output. To test
for the absence of a time expression, simply add None as a fifth element.

You can also test for particular values of attributes. Simply add pairs of
attribute name and attribute value as extra elements after the fourth element.

Note that you cannot add None as a fifth element and then add attribute-value
pairs in later elements.

"""


TIMEX_TESTS = [

    # NOTE: this one needs to be updated when we hit the next year
    ('it-is-june-5th', "It is June 5th.",
     6, 14, ('type', 'DATE'), ('value', '20160605')),

    ('sleeps-today', "John sleeps today.", 12, 17),

    ('the-year-2000', "In the year 2000 it was warm.",
     12, 16, ('type', 'DATE'), ('value', '2000')),

]
