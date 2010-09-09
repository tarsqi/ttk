"""

Set of functions that provide some statistics on Tarsqi Python modules
and TimeML files.

    analyse_modules()
    get_verbchunks_with_timexes(dir)
    get_slink_syntax(dir)


"""

import sys
import os

from types import ClassType, FunctionType, MethodType

from docmodel.xml_parser import Parser
from utilities.converter import FragmentConverter
from modules import MODULES


COUNTS = { 'modules': 0,
           'documented modules': 0,
           'undocumented modules': 0,
           'classes': 0,
           'documented classes': 0,
           'undocumented classes': 0,
           'functions': 0,
           'documented functions': 0,
           'undocumented functions': 0 }


def analyse_module(module):
    global COUNTS
    docflag = doc_flag(module.__doc__)
    COUNTS['modules'] += 1
    COUNTS[docflag + ' modules'] += 1
    print "\n<MODULE %s %s>" % (docflag, module.__name__)
    for class_object in get_classes(module):
        analyze_class(class_object)
    for (name, fun) in get_functions(module):
        analyze_function(name, fun, '  ')

def analyze_class(class_object, print_documentation=False):
    global COUNTS
    docflag = doc_flag(class_object.__doc__)
    COUNTS['classes'] += 1
    COUNTS[docflag + ' classes'] += 1
    print "  <CLASS %s %s>" % (docflag, class_object)
    for (name,fun) in get_functions(class_object):
        analyze_function(name, fun, '    ')

def analyze_function(function_name, function_object, spacing):
    global COUNTS
    docflag = doc_flag(function_object.__doc__)
    COUNTS['functions'] += 1
    COUNTS[docflag + ' functions'] += 1
    print "%s<FUNCTION %s %s>" % (spacing, docflag, function_name)

def get_classes(module):
    classes = []
    for (key, val) in module.__dict__.items():
        if type(val) == ClassType:
            if val.__dict__['__module__'] == module.__name__:
                classes.append(val)
    return classes

def get_functions(class_object):
    functions = []
    for (key, val) in class_object.__dict__.items():
        if type(val) == FunctionType:
            functions.append([key,val])
    return functions
            
def doc_flag(docstring):
    if docstring:
        return 'documented'
    else:
        return 'undocumented'

def write_counts():
    p1 = 100 * COUNTS['documented modules'] / COUNTS['modules']
    p2 = 100 * COUNTS['documented classes'] / COUNTS['classes']
    p3 = 100 * COUNTS['documented functions'] / COUNTS['functions']
    print "\nMODULES           %3d\n" % COUNTS['modules']
    print "    documented    %3d  (%d%s)" % (COUNTS['documented modules'], p1, '%')
    print "    undocumented  %3d" % COUNTS['undocumented modules']
    print "\nCLASSES           %3d\n" % COUNTS['classes']
    print "    documented    %3d  (%d%s)" % (COUNTS['documented classes'], p2, '%')
    print "    undocumented  %3d" % COUNTS['undocumented classes']
    print "\nFUNCTIONS         %3d\n" % COUNTS['functions']
    print "    documented    %3d  (%d%s)" % (COUNTS['documented functions'], p3, '%')
    print "    undocumented  %3d\n" % COUNTS['undocumented functions']

    
def analyse_modules():
    """Analyze all Tarsqi Python modules and print some documentation
    statistics for all modules, classes and functions."""
    for module in MODULES:
        analyse_module(module)
    write_counts()





    

class TimemlStats:
    
    """Class that collects and prints statistics of all files in a
    directory. Defines a method for general statistics on tags and
    tokens as well as a few more specialized methods."""

    def __init__(self, dir, extension=''):
        
        self.dir = dir
        self.extension = extension
        self.token_data = {}
        self.tag_data = { 'ALINK': { 'total': 0, 'data': {} },
                          'SLINK': { 'total': 0, 'data': {} },
                          'TLINK': { 'total': 0, 'data': {} },
                          's': { 'total': 0, 'data': {} },
                          'lex': { 'total': 0, 'data': {} },
                          'EVENT': { 'total': 0, 'data': {} },
                          'MAKEINSTANCE': { 'total': 0, 'data': {} },
                          'SIGNAL': { 'total': 0, 'data': {} },
                          'TIMEX3': { 'total': 0, 'data': {} } }

    def get_files(self):
        """Returns all the files in the directory, as long as they end in the
        specified extension."""
        files = []
        for file in os.listdir(self.dir):
            if file.endswith(self.extension):
                infile = dir + os.sep + file
                if os.path.isfile(infile):
                    files.append(infile)
        return files
    
    def print_stats(self):
        """Collect and print the standard statistics."""
        self.collect_data()
        self.print_tag_data()
        self.print_token_data()

    def collect_data(self):
        """Collect tag and token data for each file and add them instance
        variables."""
        for file in self.get_files():
            sys.stderr.write(file+"\n")
            tml_file = TimemlFile(file)
            tml_file.collect_tag_data(self.tag_data)
            tml_file.collect_token_data(self.token_data)

    def print_tag_data(self):
        print "\n\n" + '=' * 70
        print "STATISTICS FOR ", self.dir
        print  '=' * 70 + "\n"
        for tag in self.tag_data.keys():
            print "\n%s  %d\n" % (tag, self.tag_data[tag]['total'])
            keys = self.tag_data[tag]['data'].keys()
            keys.sort()
            for data in keys:
                print "  %4s  %s" % ( self.tag_data[tag]['data'][data], data )

    def print_token_data(self):
        print "\nNumber of tokens embedded in tags\n";
        for (key, val) in self.token_data.items():
            print "   %-12s %6d" % (key, val)
        print

    def get_verbchunks_with_timexes(self):
        """Print all verb chunks that contain a timex tag. Requires chunked
        input."""
        for file in self.get_files():
            xmldoc = Parser().parse_file(open(file))
            doctree = FragmentConverter(xmldoc, file).convert()
            for sentence in doctree:
                for element in sentence:
                    if element.isVerbChunk() and element.get_timex():
                        element.pretty_print()

    def get_slink_syntax(self):
        """Print the systax values of all slinks."""
        syntax_vals = {}
        for file in self.get_files():
            xmldoc = Parser().parse_file(open(file))
            slinks = xmldoc.get_tags('SLINK')
            for slink in slinks:
                synval = slink.attrs.get('syntax')
                if syntax_vals.has_key(synval):
                    syntax_vals[synval] += 1
                else:
                    syntax_vals[synval] = 1
        print "\nSyntax values in all SLINKS:\n"
        for pattern in syntax_vals.keys():
            print "   %6d   %s" % (syntax_vals[pattern], pattern)


class TimemlFile:

    """Class that contains methods for collecting some statistics for a
    TimeML file."""

    def __init__(self, filename):
        """Create the XmlDocument for filename."""
        self.xmldoc = Parser().parse_file(open(filename))

    def collect_tag_data(self, tag_data):
        """Add data on TimeML tags, as well as a few others (s and lex) to the
        tag_data object."""
        
        for alink in self.xmldoc.get_tags('ALINK'):
            tag_data['ALINK']['total'] += 1
            val = alink.attrs.get('syntax')
            self._increment_tag_data_val(tag_data, 'ALINK', val)

        for slink in self.xmldoc.get_tags('SLINK'):
            tag_data['SLINK']['total'] += 1
            val = slink.attrs.get('syntax')
            self._increment_tag_data_val(tag_data, 'SLINK', val)

        for tlink in self.xmldoc.get_tags('TLINK'):
            tag_data['TLINK']['total'] += 1
            val = tlink.attrs.get('origin','')
            if val.startswith('CLASSIFIER'):
                val = 'CLASSSIFIER'
            self._increment_tag_data_val(tag_data, 'TLINK', val)

        tag_data['s']['total'] += len(self.xmldoc.get_tags('s'))
        tag_data['lex']['total'] += len(self.xmldoc.get_tags('lex'))
        tag_data['EVENT']['total'] += len(self.xmldoc.get_tags('EVENT'))
        tag_data['MAKEINSTANCE']['total'] += len(self.xmldoc.get_tags('MAKEINSTANCE'))
        tag_data['SIGNAL']['total'] += len(self.xmldoc.get_tags('SIGNAL'))
        tag_data['TIMEX3']['total'] += len(self.xmldoc.get_tags('TIMEX3'))

    def _increment_tag_data_val(self, tag_data, tag, val):
        old_total = tag_data[tag]['data'].get(val, 0)
        tag_data[tag]['data'][val] = old_total + 1

    def collect_token_data(self, token_counts):
        tag_stack = ['ALL']
        for element in self.xmldoc:
            if element.is_opening_tag():
                tag_stack.append(element.tag)
            elif element.is_closing_tag():
                tag_stack.pop()
            else:
                count = len( element.content.split())
                for tag in tag_stack:
                    old_total = token_counts.get(tag, 0)
                    token_counts[tag] = old_total + count

        

if __name__ == '__main__':

    dir = 'data/out/rte3'
    dir = 'data/out/timebank-gut'
    dir = '/Users/marc/Desktop/aquaint/5/N35'

    analyse_modules()
    
    #stats = TimemlStats(dir, 'tml')
    #stats.print_stats()
    #stats.get_verbchunks_with_timexes()
    #stats.get_slink_syntax()


