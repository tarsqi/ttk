"""

Make sure that TTK_ROOT environment variable is set.

This is ugly, but we need to do this because create_vectors imports the method
create_gold_vectors, which is in the components package which requires TTK_ROOT.

"""

# TODO: would like to find a way to redo what components.__init__ does because
# it is at the source of these troubles.

import os

os.environ['TTK_ROOT'] = '../..'
