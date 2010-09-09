import os
from types import IntType

from ttk_path import TTK_ROOT


TESTCASES_DIR = os.path.join(TTK_ROOT, 'testing', 'cases')
REPORTS_DIR = os.path.join(TTK_ROOT, 'testing', 'reports')
DATA_DIR = os.path.join(TTK_ROOT, 'testing', 'tmp')




def load_mappings(path):

    """Loads a file with test cases into a dictionary. The input file
    looks as follows:

       VERSION=N.N
       DATE=YYYYMMDD

       001: <description>
       <input>
       <expected output>

       002: <description>
       <input>
       <expected output>
       
    The dictionary is indexed on the id:

    { id1: { 'description': <string>, 'input': <string>, 'output': <string> }
      id2: ...
      id3: ... }

    Arguments:
       path - an absolute path 
    Returns:
       a Dictionary"""
    
    INPUT = 1
    OUTPUT = 2
    mappings = {}
    fh = open(path,'r')

    next = None
    for line in fh:
        if line.startswith('VERSION'):
            continue
        elif line.startswith('DATE'):
            continue
        elif line.strip() == '':
            continue
        elif line.strip().startswith('#'):
            continue
        elif line[3] == ':' and type(eval(line[:3])) == IntType:
            (id, description) = (line[0:3], line[4:].strip())
            mappings[id] = { 'description': description }
            next = INPUT
        elif next == INPUT:
            mappings[id]['input'] = line.strip()
            next = OUTPUT
        elif next == OUTPUT:
            mappings[id]['output'] = line.strip()
            next = None

    return mappings
