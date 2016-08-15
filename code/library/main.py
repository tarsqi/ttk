"""Initial experiments on loading the libraries.

Libraries are now all Python code and are use through imports. The idea is to
have libraries defined independently from the implementation, defining a syntax
for all libraries (simple settings, rules, etcetera) and then read in the
libraries (maybe in a lazy fashion).

The TarsqiLibrary class is added to the Tarsqi instance and handed over to the
TarsqiDocument instance.

"""

import os

TTK_ROOT = os.environ['TTK_ROOT']

TIMEML_SPECS = os.path.join(TTK_ROOT, 'library', 'timeml.txt')


class TarsqiLibrary(object):

    def __init__(self, tarsqi_instance):
        # the timeml instance variable is replacing the timeMLspec module
        self.timeml = TimeMLSpecs(tarsqi_instance)


class TimeMLSpecs(object):

    def __init__(self, tarsqi_instance):
        for line in open(TIMEML_SPECS):
            line = line.strip()
            comment_start = line.find('#')
            if comment_start > -1:
                line = line[:comment_start]
            if line:
                var, value = parse_line(line)
                setattr(self, var, value)


def parse_line(line):
    """Parse a line with a simple variable assignment."""
    var, value = line.split('=')
    var = var.strip()
    value = value.strip()
    if value[0] == '[':
        value = [v.strip() for v in value.strip('[]').split(',')]
    return var, value
