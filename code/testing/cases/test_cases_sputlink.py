"""

SputLink tests use the simplified constraints based on identifiers (instead of
events and times). A constraint is a tuple of strings. A test case has a name,
an input (a list of constaints) and an expected utput (a list of constraints).

The test code requires the expected output in the case to be identical to the
observed output (both are sorted before comparison).

"""


class Case(object):

    def __init__(self, description, constraints, result):
        self.description = description
        self.constraints = constraints
        self.result = result


SPUTLINK_TESTS = [

    Case("nothing-happening",

         [('1', '<', '2'), ('3', '<', '4')],

         [('1', '<', '2'), ('3', '<', '4'), ('2', '>', '1'), ('4', '>', '3')]),

    Case("inconsistency-before-and-after",

         [('1', '<', '2'), ('2', '<', '1')],

         [('1', '<', '2'), ('2', '>', '1')]),

    Case("before-before",

         [('1', '<', '2'), ('2', '<', '3')],

         [('1', '<', '2'), ('2', '<', '3'), ('1', '<', '3'),
          ('2', '>', '1'), ('3', '>', '2'), ('3', '>', '1')]),

    Case("before-during-during",

         [('1', '<', '2'), ('2', 'd', '3'), ('3', 'd', '4')],

         [('1', '<', '2'), ('2', 'd', '3'), ('3', 'd', '4'),
          ('2', '>', '1'), ('3', 'di', '2'), ('4', 'di', '3'),
          ('2', 'd', '4'), ('4', 'di', '2'),
          ('1', '< d m o s', '3'), ('3', '> di mi oi si', '1'),
          ('1', '< d m o s', '4'), ('4', '> di mi oi si', '1')]),

]
