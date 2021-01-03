from __future__ import absolute_import
from __future__ import print_function
import os
import sys
import re
from io import open

search_term = sys.argv[1]


def search_file(name, search_term):
    with open(name) as fh:
        line_number = 0
        for line in fh:
            line_number += 1
            line = line.strip()
            if line.startswith('#'):
                continue
            if search_term in line:
                loc = "%s:%d" % (name, line_number)
                print(("%-30s  ==  %s" %  (loc, line)))


for root, dirs, files in os.walk(".", topdown=False):
    for name in files:
        path = os.path.join(root, name)
        if 'deprecated/' in path or 'FSA-org' in path:
            continue
        if name.endswith('.py'):
            search_file(path, search_term)
