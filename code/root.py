"""root.py

All this module does is to set the TTK_ROOT environment variable.

Previously, this was done inline for all the modules that needed it, but this
resulted in an ugly situation where a piece of code was inserted inbetween a set
of import statements.

"""

# TODO: I do not like this, is there a better way to deal with this?


import os

scriptPath = os.path.abspath(__file__)
TTK_ROOT = os.path.dirname(scriptPath)
os.environ['TTK_ROOT'] = TTK_ROOT
