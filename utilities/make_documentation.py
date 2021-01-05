"""make_documentation.py

Create manual pages with the docstrings for modules, classes and functions,
using the modules listed in modules.py.

To update the documentation run this script from the directory it is in.

This code was written because pydoc breaks on some of the tarsqi modules, most
notably those that import the treetagger.


USAGE:

Run this from the parent directory with the -m option

$ python -m utilities.make_documentation


TODO:

- the code does not deal with class methods, see for example TagId in
  components.preprocessing.wrapper.

- At some point the code created potentially undesired documentation for the
  module components.preprocessing.wrapper, adding a couple of module-level
  functions that are not in the code, but are imported functions. This has
  seized to be the case for that module, but it is not clear why.

- Check whether pydoc still chokes in tarsqi code

"""


from __future__ import absolute_import
from __future__ import print_function
import os
import sys
import inspect
from types import FunctionType, MethodType

from .modules import MODULES
from io import open
import six

# Set this to True if you want the sources for all functions written to files
# that are linked to from the module page, this slows down the code quite a bit
# and requires 6MB more space.
WRITE_FUNCTION_SOURCES = False

# With this one set to True, private functions (those that start with a single
# underscore) are included.
PRINT_PRIVATE_FUNCTIONS = True

# directory where the documentation is written
DOCUMENTATION_DIR = os.path.join('docs', 'code')


javascript_code = u"""<script language="JavaScript" type="text/JavaScript">
<!--
function view_code(id) {
  var newurl = "../functions/" + id + ".html";
  var w = window.open(newurl,"source code","width=770,height=600,
                      scrollbars=yes,resizable=yes");
  w.xopener = window;
}
//-->
</script>
"""

FUNCTION_ID = 0


def print_module_documentation(module):
    print(module.__name__)
    filename = os.path.join(DOCUMENTATION_DIR, 'modules',
                            module.__name__ + '.html')
    docfile = open(filename, 'w')
    docfile.write(u"<html>\n<head>\n")
    docfile.write(u'<link href="../css/module.css"' +
                  u' rel="stylesheet" type="text/css">' + "\n")
    docfile.write(javascript_code)
    docfile.write(u"</head>\n<body>\n")
    docfile.write(u'<a href=../index.html>index</a>' + "\n\n")
    docfile.write(u'<div class="title">module ' +
                  module.__name__ + u"</div>\n\n")
    module_classes = get_classes(module)
    if module_classes:
        docfile.write(u"<pre>\n")
        for module_class in module_classes:
            docfile.write(u"<a href=#%s>%s</a>\n"
                          % (module_class.__name__, module_class.__name__))
        docfile.write(u"</pre>\n\n")
    docstring = get_docstring(module)
    if docstring:
        docfile.write(u"<pre>\n" + docstring + "</pre>\n\n")
    print_class_documentation(docfile, module_classes)
    print_function_documentation(docfile, get_module_functions(module))


def print_class_documentation(docfile, classes):
    for class_object in classes:
        (module_name, class_name) = get_module_and_class_name(class_object)
        docfile.write(u"\n" + u'<a name="' + class_name + '"/>')
        docfile.write(u'<div class="section">class ' + class_name + "</div>\n")
        docfile.write(u"<pre>\n")
        docstring = get_docstring(class_object)
        for base_class in class_object.__bases__:
            (module_name, class_name) = get_module_and_class_name(base_class)
            ref = module_name + u'.html#' + class_name
            if module_name == '__builtin__':
                href = class_name
            else:
                href = u"<a href=%s>%s</a></strong>" % (ref, class_name)
            docfile.write(u"<strong>Inherits from: %s</strong>\n" % href)
        if docstring:
            docfile.write(u"\n" + docstring)
        docfile.write(u"</pre>\n\n")
        functions = get_class_functions(class_object)
        functions.sort(key=lambda x: x[0])
        public_functions = get_public_functions(functions)
        private_functions = get_private_functions(functions)
        if public_functions:
            docfile.write(u"<blockquote>\n")
            docfile.write(u"<h3>Public Functions</h3>\n")
            for (name, fun) in public_functions:
                print_function(name, fun, docfile)
            docfile.write(u"</blockquote>\n")
        if private_functions and PRINT_PRIVATE_FUNCTIONS:
            docfile.write(u"<blockquote>\n")
            docfile.write(u"<h3>Private Functions</h3>\n")
            for (name, fun) in private_functions:
                print_function(name, fun, docfile)
            docfile.write(u"</blockquote>\n")


def print_function_documentation(docfile, functions):
    if functions:
        docfile.write(u"\n%s\n" % u'<div class="section">module functions</div>')
    functions.sort(key=lambda x: x[0])
    for (name, fun) in get_public_functions(functions):
        print_function(name, fun, docfile)


def get_classes(module):
    classes = []
    for (key, val) in module.__dict__.items():
        if type(val) == type:
            # ignore those that do not have the right module mentioned in their
            # dictionary, this also gets rid of things like ListType, which do
            # not have a value for __module__
            if val.__dict__.get('__module__') == module.__name__:
                classes.append(val)
    classes.sort(key=lambda x: str(x))
    return classes


def get_module_functions(module):
    functions = []
    for (key, val) in module.__dict__.items():
        if type(val) == FunctionType:
            if inspect.getmodule(val) is module:
                functions.append([key, val])
    return functions


def get_class_functions(class_object):
    functions = []
    for (key, val) in class_object.__dict__.items():
        if type(val) == FunctionType:
            functions.append([key, val])
    return functions


def get_public_functions(functions):
    public_functions = []
    for (name, fun) in functions:
        if name.startswith('__') or not name.startswith('_'):
            public_functions.append((name, fun))
    return public_functions


def get_private_functions(functions):
    private_functions = []
    for (name, fun) in functions:
        if name.startswith('_') and not name.startswith('__'):
            private_functions.append((name, fun))
    return private_functions


def print_function(name, fun, docfile):
    global FUNCTION_ID
    funname = get_function_name(fun)
    docstring = get_docstring(fun)
    docfile.write(u"<pre>\n")
    docfile.write(u"<div class=function>%s</div>\n" % funname)
    docfile.write(docstring)
    FUNCTION_ID += 1
    identifier = u"%04d" % FUNCTION_ID
    if WRITE_FUNCTION_SOURCES:
        if docstring:
            docfile.write(u"\n\n")
        docfile.write(u"<a href=javascript:view_code(\"%s\")>view source</a>"
                      % identifier)
        funname = get_function_name(fun)
        print_function_code(identifier, funname, fun)
    docfile.write(u"</pre>\n")


def get_function_name(fun):
    done = False
    lines = inspect.getsourcelines(fun)[0]
    name = []
    while not done:
        name.append(lines.pop(0).strip())
        if name[-1].endswith('):'):
            done = True
    return ' '.join(name)[4:-1]


def print_function_code(identifier, name, fun):
    filename = os.path.join(DOCUMENTATION_DIR,
                            u'functions', u"%s.html" % identifier)
    funfile = open(filename, "w")
    funfile.write(u"<html>\n<head>\n")
    funfile.write(u'<link href="../css/function.css"')
    funfile.write(u' rel="stylesheet" type="text/css">' + "\n")
    funfile.write(u"</head>\n<body>\n")
    funfile.write(u'<pre>')
    try:
        code = "".join(inspect.getsourcelines(fun)[0])
    except IOError:
        print("WARNING: could not get source code of %s" % fun)
        code = ''
    code = trim(code, 0)
    code = code.replace('<', '&lt;')
    funfile.write(code)
    funfile.write(u'</pre>')


def get_docstring(object):
    docstring = u''
    if object.__doc__:
        docstring = object.__doc__
    return six.text_type(trim(protect(docstring)))


def print_docstring(object, docfile, prefix=''):
    docstring = get_docstring(object)
    docfile.write(u"<pre>\n" + docstring)
    if type(object) == FunctionType:
        global FUNCTION_ID
        FUNCTION_ID += 1
        identifier = "%04d" % FUNCTION_ID
        if docstring:
            docfile.write(u"\n\n")
        docfile.write(u"<a href=javascript:view_code(\"%s\")>view source</a>"
                      % identifier)
        funname = get_function_name(object)
        print_function_code(identifier, funname, object)
    docfile.write(u"</pre>\n")


def protect(docstring):
    docstring = docstring.replace('<', '&lt;')
    docstring = docstring.replace('>', '&gt;')
    docstring = docstring.strip()
    return docstring


def get_module_and_class_name(base_class):
    return (base_class.__module__, base_class.__name__)


def trim(docstring, linenum=1):
    if not docstring:
        return ''
    # Convert tabs to spaces (following the normal Python rules)
    # and split into a list of lines:
    lines = docstring.expandtabs().splitlines()
    # Determine minimum indentation (first line doesn't count for
    # docstrings):
    indent = sys.maxsize
    for line in lines[linenum:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))
    # Remove indentation (first line is special):
    trimmed = [lines[0].strip()]
    if indent < sys.maxsize:
        for line in lines[1:]:
            trimmed.append(line[indent:].rstrip())
    # Strip off trailing and leading blank lines:
    while trimmed and not trimmed[-1]:
        trimmed.pop()
    while trimmed and not trimmed[0]:
        trimmed.pop(0)
    # Return a single string:
    return '\n'.join(trimmed)


if __name__ == '__main__':

    filename = os.path.join(DOCUMENTATION_DIR, 'index.html')
    indexfile = open(filename, 'w')
    indexfile.write(u"<html>\n<head>\n")
    indexfile.write(u"<link rel=\"stylesheet\" href=\"css/list.css\"> \n")
    indexfile.write(u"</head>\n<body>\n")
    indexfile.write(u"<h3>Tarsqi Toolkit Module Documentation</h3>\n")
    indexfile.write(u"<ul>\n")
    for module in MODULES:
        name = module.__name__
        # if not name.startswith('lib'): continue
        indexfile.write(u"<li><a href=modules/%s.html>%s</a>\n" % (name, name))
        print_module_documentation(module)
    indexfile.write(u"</ul>\n</body>\n</html>\n")
