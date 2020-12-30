
# Porting to Python 3

December 2020.

This document has notes on the effort to get a Python 3 version of TTK. Originally, the goal was to get a few steps along the way without any impact to TTK users, that is, no extra installations, not even something as simple as `pip install future` or `pip install builtins`. The goal was also to eventually change the code so that it supports both Python 2.7 and Python 3.5 and up.

This was all dropped. The goal is to get a Python3 version in TTK version 3.0.0. Period. Probably version 3.6. This might require extra installation, fine. And version 2.7 will not be supported anymore from now on except perhaps for requested bug fixes on version 2.2.0. Having said that, the first steps of the process are all steps where the resulting code will still run on Python 2.7.




## 1. Process

For now:

- Started branch `79-python3`.
- Following the steps in [https://portingguide.readthedocs.io/en/latest/process.html](https://portingguide.readthedocs.io/en/latest/process.html)

  - After each step, review the changes, do not yet make any manual edits
  - After one or more steps, run the tests and if they pass put all changes in the git staging area.
  - Try to isolate automatic amd manual changes in separate commits. The only exception are:
    - A porting issue where a automatic step is followed by well-defined manual steps, these sometimes make more sense in just one commit. 
    - This file may be updated in a commit alongside automatic changes, typically changes are relevant to the porting issue of the commit.
- Also looking at [http://python3porting.com/preparing.html](http://python3porting.com/preparing.html) to do those preparatory changes that allow you to still run under Python2 (division, strings, new classes, etcetera). There obviously is major overlap between this one and the previous one.
- Commands that give information:

  -  `python-modernize` to give hints on the idioms to change.
    - probably using individual fixers
  -  `pylint --py3k` for more hints on Python3 compatibility.
  -  `python -3` when running tarsqi.py and the testing and regression scripts.
- Use `2to3` [http://python3porting.com/2to3.html](http://python3porting.com/2to3.html) for the final mechanichal steps, many of them probably already done in the previous steps. Will probably also want to get rid of all the future imports. Look at [https://adamj.eu/tech/2019/03/13/dropping-python-2-support/](https://adamj.eu/tech/2019/03/13/dropping-python-2-support/) for some notes on dropping Python 2 support.
- At the very end, test this on a new clone. There could be issues like updating libraries that have slipped through the cracks.


In the following, each section corresponds to one or more commits on the `79-python3` branch.



## 2.  Initial syntax changes

These changes are based on https://portingguide.readthedocs.io/en/latest/syntax.html. All changes made in this section are in commit [94b2bce5](https://github.com/tarsqi/ttk/commit/94b2bce5e5b68e688d4d385bcb2b022b4f1e7093).

### 2.1.  Getting rid of tabs

```
find . -name '*.py' -type f -exec bash -c 'T=$(mktemp); expand -i -t 8 "$0" > "$T" && mv "$T" "$0"' {} \;
```

That command failed however. But the only file with tabs is `utilities/wordnet.py`. That file is not needed by the runtime version and would only be needed to rebuild libraries (see `build_event_nominals1.py` and `build_event_nominals2.py`). Won't worry about this, if libraries need to be rebuild use old version or use the WordNet code incloded in CoreLex or NLTK. Note also that the WordNet code is somewhat fragile and inconsistent in how it finds its data.

Instead of the above command I used

```
$ perl -p -e 's/\t/        /g' wordnet.py > wordnet.new.py
$ rm wordnet.py
$ mv wordnet.new.py wordnet.py
```

No problems with that.

### 2.2.  Tuple Unpacking in Parameter Lists

```
$ python-modernize -wnf lib2to3.fixes.fix_tuple_params .
```

This only changed `utitlities/FSA.py` and `utitlities/FSA-org.py`. All regular tests passed after that, but I am not sure that they used the FSA so should do some testing here.

Tried to run it in isolation, replacing `from utilities import logger` with `import logger`. The changes were in four methods. Three work fine:

```python
>>> from FSA import *
>>> fsa2 = compileOP( [ 'a','(','b','|','c','*',')' ] )
>>> fsa3 = compileOP(['(','a','|','the',')', 'very', '*', '(', 'boring','|','nice', ')', '+', 'movie'])
>>> >>> union(fsa2, fsa3)
<FSA.FSA instance>
>>> completion(fsa3)
<FSA on [_'_(_'_,_ _'_a_'_,_ _'_|_'_,_ _'_t_h_e_'_,_ _'_)_'_,_ _'_v_e_r_y_'_,_ _'_*_'_,_ _'_(_'_,_ _'_b_o_r_i_n_g_'_,_ _'_|_'_,_ _'_n_i_c_e_'_,_ _'_)_'_,_ _'_+_'_,_ _'_m_o_v_i_e_'_]>
>>> fsa3.determinized()
<FSA on [_'_(_'_,_ _'_a_'_,_ _'_|_'_,_ _'_t_h_e_'_,_ _'_)_'_,_ _'_v_e_r_y_'_,_ _'_*_'_,_ _'_(_'_,_ _'_b_o_r_i_n_g_'_,_ _'_|_'_,_ _'_n_i_c_e_'_,_ _'_)_'_,_ _'_+_'_,_ _'_m_o_v_i_e_'_]>
```

But:

```python
>>> reverse(fsa3)
TypeError: __init__() takes at least 6 arguments (5 given)
```

Sadly, there are two cases where reverse() seems to be used:

```
>>> grep -n -e 'reverse(' */*/*.py

components/common_modules/constituent.py:302:        alinkedEventContext.reverse()
components/common_modules/constituent.py:364:        event_context.reverse()
```

it is used for finding backward slinks and alinks.

However, it turns out that this error also happens with the code before this change, so I will let it go.

### 2.3.   Backticks and other changes

The following fixes backtics and there were no problems with it:

```
$ python-modernize -wnf lib2to3.fixes.fix_repr .
```

There was no need to remove the inequality operator `<>` and there were no assignments to True or False. Other syntax changes are done in later steps.



## 3. More preparatory changes

Based on [http://python3porting.com/preparing.html](http://python3porting.com/preparing.html). These are similar to the above in that they allow the code to still run on Python 2.7.

### 3.1.  Division of integers

Using // when we really want to have integers as the result, using / in other cases. Sometimes using `from __future__ import division` and removing explicit conversions into floats. See commit [047d9c28](https://github.com/tarsqi/ttk/commit/047d9c2850b5589e05641e182f69704f8787bb09).

### 3.2.  Using new style classes

Doing this all manually, but used the following code to find the classes.

```python
import os

def check_classes(fname):
    with open(fname) as fh:
        for line in fh:
            line = line.strip()
            if line.startswith('class ') and line.endswith(':'):
                if is_old_class(line):
                    print(fname, '>>>', line)
                if has_multiple_parents(line):
                    print(fname, '===', line)

def is_old_class(line):
    return '(' not in line or line.endswith('():')

def has_multiple_parents(line):
    return ',' in line

if __name__ == '__main__':
    for root, dirs, files in os.walk(".", topdown=False):
        for name in files:
            if name.endswith('.py'):
                check_classes(os.path.join(root, name))
```

TTK does not use mulitple inheritance so I did not need to worry about the MRO. The only thing that needed some time was to figure out how to do the FSA code since allegedly its error handling depends on old style classes. Well, it doesn't, it is just that there was a part in the code that relied on things like *Constituent* being of type *types.InstanceType*:

```python
if (type(input) is InstanceType and
    input.__class__.__name__ in ['Constituent', 'Chunk', 'NounChunk',
                                 'VerbChunk', 'Token', 'AdjectiveToken',
	                               'EventTag', 'TimexTag']):
```

This was replaced with

```python
if getattr(input, '__class__').__name__ in [
    'Constituent', 'Chunk', 'NounChunk', 'VerbChunk',
    'Token', 'AdjectiveToken', 'EventTag', 'TimexTag']:
```

WIth this fixed no errors were raised. There are issues however with raising errors in `FSA.py`, they will need to be dealt with in a later step.

More seriously, when `FSA.FSA` and `FSA.Sequence` are turned into new style classes, code starts crashing on loading pickle files. I needed to re compile Evita and Slinket patterns:

```
$ cd library/evita
$ python2 compile_patterns.py
$ cp *.pickle patterns
```

```
$ cd library/slinket
$ python2 create_dicts.py
$ cp *.pickle dictionaries
```

After this it all worked, but see the TODO comment in `create_dicts.py` which elaborates a bit on the ugly hack I used.

See commit [0ccd82d9](https://github.com/tarsqi/ttk/commit/0ccd82d9f11e72c75b7bcbb5e71044b87a818385).

### 3.3.  Absolute imports

Changed made here are based on [https://portingguide.readthedocs.io/en/latest/imports.html](https://portingguide.readthedocs.io/en/latest/imports.html).

```
$ python-modernize -wnf libmodernize.fixes.fix_import .
```

This made many changes, importing from future and changing other imports. One weird change is that pretty much every line in `componets/blinker/compare.py ` is changed. Not sure what is going on there, but when getting the previous version and comparing it to the one after the patch, all I see is a difference in the line with the future import.

There are no occurrences of "import *" in functions and no import cycles that I am aware of.

See commit [038ec101](https://github.com/tarsqi/ttk/commit/038ec101a197840f92ba492a064a7d452b0ed501).

After this I made some changes to streamline some of the utilities and testing scripts, including removing the annoying *path* module and updating the documentation on running the scripts. Previsously, scripts like `testing/run_tests.py` ran from the directory they are in and they relied on separate scrappy module to manipulate the path. That started to fail after the import updates so I removed the path cludge and changed the documentation to reflect the new way of calling the scripts from the parent directory: 

```
$ python -m testing.run_tests
```

See commit [465f9dfc](https://github.com/tarsqi/ttk/commit/465f9dfcdb6ef4b5051d6d5732f1ef116c4486f6).

### 3.4.  String handling

Changed made here are based on [https://portingguide.readthedocs.io/en/latest/strings.html](https://portingguide.readthedocs.io/en/latest/strings.html). See commit [c378f688](https://github.com/tarsqi/ttk/commit/c378f688321ff52111325f29ad7c705cf1292923) for all changes made in this section.

For separating binary data and strings I glanced over all the lines with quoted strings in them, they all appear to be text strings. Did this for cases like `"hello"` with the find.pl script and created find.py to do the same for use of `'string'`, `u"string"`, `u'string'`, byte strings with the b prefix and the raw string.

String operations in Python 3 cannot mix different types, look into this. Using -3 on the tarsqi.py script and run_tests.py gives 2 warnings on Blinker code:

```
compare.py:150: DeprecationWarning: comparing unequal types not supported in 3.x
  if (year1_int < year2_int):
compare.py:152: DeprecationWarning: comparing unequal types not supported in 3.x
  elif (year1_int > year2_int):
```

However, looking at the code it seems that both variables must be of type *int*.

For type checking (use of basestring) I ran

```
$ python-modernize -wnf libmodernize.fixes.fix_basestring .
```

which didn't make any changes.

#### 3.4.1  File I/O

```
$ python-modernize -wnf libmodernize.fixes.fix_open .
```

This caused many changes, most are to add

```python
from io import open
```

We do get some problems, here's the first:

```
python tarsqi.py data/in/simple-xml/tiny.xml out.xml 
Traceback (most recent call last):
  File "tarsqi.py", line 111, in <module>
    from components import COMPONENTS, valid_components
  File ".../ttk/git/ttk/components/__init__.py", line 6, in <module>
    from preprocessing.wrapper import PreprocessorWrapper
  File ".../ttk/git/ttk/components/preprocessing/wrapper.py", line 28, in <module>
    from components.preprocessing.chunker import chunk_sentences
  File ".../ttk/git/ttk/components/preprocessing/chunker.py", line 30, in <module>
    from components.common_modules.tree import create_tarsqi_tree
  File ".../ttk/git/ttk/components/common_modules/tree.py", line 9, in <module>
    from components.common_modules.chunks import NounChunk, VerbChunk
  File ".../ttk/git/ttk/components/common_modules/chunks.py", line 24, in <module>
    from components.evita import bayes
  File ".../ttk/git/ttk/components/evita/bayes.py", line 16, in <module>
    DictSemcorContext = open_pickle_file(forms.DictSemcorContextPickleFilename)
  File ".../ttk/git/ttk/utilities/file.py", line 45, in open_pickle_file
    return pickle.load(fh)
  File ".../miniconda2/lib/python2.7/pickle.py", line 1384, in load
    return Unpickler(file).load()
  File ".../miniconda2/lib/python2.7/pickle.py", line 864, in load
    dispatch[key](self)
  File ".../miniconda2/lib/python2.7/pickle.py", line 986, in load_unicode
    self.append(unicode(self.readline()[:-1],'raw-unicode-escape'))
TypeError: decoding Unicode is not supported
```

The problem here is in the code that loads a pickle file (`utilities/file.py`), which reads a native string where it should read a binary string, change `open_pickle_file()` into 

```python
def open_pickle_file(fname):
    """Return the contents of a pickle file."""
    with open(fname, 'r') as fh:
        return pickle.load(fh)
```

The next problem is in the logger: 

```
  File ".../ttk/git/ttk/utilities/logger.py", line 76, in __init__
    self.html_file.write("<html>\n")
TypeError: write() argument 1 must be unicode, not str
```

While this would work fine in Python3, in Python 2 the string has to be of type unicode and the string literal is not that type so we need to add a `u` in front of it.

And then:

```
  File ".../ttk/git/ttk/docmodel/source_parser.py", line 218, in parse_file
    self.parser.ParseFile(open(filename))
TypeError: read() did not return a string object (type=unicode)
```

This could be fixed in docmodel.source_parser.SourceParserXml.parse_file, replacing

```python
self.parser.ParseFile(open(filename))
```

with

```python
content = open(filename).read()
self.parser.Parse(content)
```

Finally, the last problem:

```
  File ".../ttk/git/ttk/library/blinker/blinker_rule_loader.py", line 113, in read_syntactic_rules
    val = str.split(val[1:-1], '|')
TypeError: descriptor 'split' requires a 'str' object but received a 'unicode'
```

Blinker contained an ancient line that used str.split(), replaced it with

```python
val = val[1:-1].split('|')
```

And finally the tarsqi script works and so does the basic test script and the evita regression test... but not for writing the regression report, which takes us to the next section.

#### 3.4.1.  Unresolved string issue

Generating a report for the regression tests croaks the same way as the logger:

```
$ python -m testing.regression --report
...
  File ".../ttk/git/ttk/testing/regression.py", line 181, in write_index
    self.index_fh.write("<html>\n<body>\n")
TypeError: write() argument 1 must be unicode, not str
```

This will probably show up all over the place. The annoying part is that the code would work fine on Python3 but to make it run on Python 2 we need to track down all those string literals, which I really do not want to do. So for now we just fix it for the code I need for porting to python3, including showing the results of the regression tests (and whatever else comes up later).

### 3.5.  Exceptions

Based on [https://portingguide.readthedocs.io/en/latest/exceptions.html](https://portingguide.readthedocs.io/en/latest/exceptions.html). All changes made in this context are in commit [854baedc](https://github.com/tarsqi/ttk/commit/854baedc0417e9ed431045248fcede3649e17bf2).

```
$ python-modernize -wnf lib2to3.fixes.fix_except .
```

This introduced one change, which had to be edited manually to enter some meaningful names instead of the standard `xxx_todo_changeme`.

```
$ python-modernize -wnf libmodernize.fixes.fix_raise -f libmodernize.fixes.fix_raise_six .
```

This made a bunch of changes, usually of the following kind: 

```diff
-            raise AttributeError, name
+            raise AttributeError(name)
```

But some things gave warnings:

```
RefactoringTool: ### In file ./utilities/wordnet.py ###
RefactoringTool: Line 856: could not convert: raise "unimplemented"
RefactoringTool: Python 3 does not support string exceptions
```

Here is a list of all lines that had this problem:

```
### In file ./components/common_modules/constituent.py ###
Line 236:   raise "ERROR specifying description of pattern"

### In file ./utilities/FSA-org.py ###
Line 1641:  raise "ERROR (1): expression missing at least one '('"
Line 1373:  raise "ERROR specifying description of pattern"
Line 1332:  raise "ERROR: possibly label is in dict format, but not the input"
Line 1650:  raise "ERROR (2): expression missing at least one ')'"
Line 1881:  raise 'unimplemented'
Line 1959:  raise 'unimplemented'
Line 1733:  raise 'extra character in pattern (possibly ")" )'

### In file ./utilities/FSA.py ###
Line 1655:  raise "ERROR (1): expression missing at least one '('"
Line 1387:  raise "ERROR specifying description of pattern"
Line 1344:  raise "ERROR: possibly label is in dict format, but not the input"
Line 1664:  raise "ERROR (2): expression missing at least one ')'"
Line 1895:  raise 'unimplemented'
Line 1973:  raise 'unimplemented'
Line 1747:  raise 'extra character in pattern (possibly ")" )'

### In file ./utilities/wordnet.py ###
Line 856:   raise "unimplemented"
```

Changed those manually by wrapping Exception around all strings.

Some instances were not found by the modernize script:

```
$ python utilities/find.py 'raise '
./components/evita/features.py ==  else: raise "ERROR: unknown modal form: "+str(form)
./components/evita/features.py ==  else: raise "ERROR: unknown raise form: "+str(form)
./utilities/wordnet.py         ==  raise "unknown attribute " + key
./utilities/wordnet.py         ==  raise self.getPointers.__doc__
./utilities/wordnet.py         ==  raise self.getPointers.__doc__
```

These were also changed by hand.

All these changes resulted in some errors due to non-unicode strings being written to a file in the sputlink code (see 3.4.1), those were fixed manually.

Raising StandardError does not occur in the code.

Raising non-exceptions were all caught I think.

Removing `sys.exc_type`, `sys.exc_value`, `sys.exc_traceback`:

```
$ python utilities/find.py "sys.exc_"
./tarsqi.py       ==   % (name, sys.exc_type, sys.exc_value))
./tarsqi.py       ==   sys.stderr.write("ERROR: %s\n" % sys.exc_value)
./tarsqi.py       ==   sys.exit('ERROR: ' + str(sys.exc_value))
```

These were manually fixed.


#### 3.5.1.  Unresolved

Did not look at the exception scope case.

The command line invocation for the iteration case seems to be wrong because it was the same as for the new except syntax. Running it again did give cryptic notes on files that needed to be modified.

```
$ python-modernize -wnf lib2to3.fixes.fix_except .
```

```
RefactoringTool: Files that need to be modified:
RefactoringTool: ./tarsqi.py
RefactoringTool: ./components/blinker/main.py
RefactoringTool: ./components/classifier/vectors.py
RefactoringTool: ./components/common_modules/chunks.py
RefactoringTool: ./components/common_modules/constituent.py
RefactoringTool: ./components/common_modules/tree.py
RefactoringTool: ./components/evita/bayes.py
RefactoringTool: ./components/evita/features.py
RefactoringTool: ./components/gutime/wrapper.py
RefactoringTool: ./components/preprocessing/chunker.py
RefactoringTool: ./deprecated/xml_parser.py
RefactoringTool: ./deprecated/demo/display.py
RefactoringTool: ./docmodel/document.py
RefactoringTool: ./docmodel/main.py
RefactoringTool: ./docmodel/metadata_parser.py
RefactoringTool: ./library/classifier/create_vectors.py
RefactoringTool: ./library/evita/nominal_trainer.py
RefactoringTool: ./testing/create_slinket_cases.py
RefactoringTool: ./utilities/FSA-org.py
RefactoringTool: ./utilities/FSA.py
RefactoringTool: ./utilities/convert.py
RefactoringTool: ./utilities/make_documentation.py
RefactoringTool: ./utilities/wordnet.py
```



### 3.6.  Standard library

Based on [htps://portingguide.readthedocs.io/en/latest/stdlib-reorg.html](tps://portingguide.readthedocs.io/en/latest/stdlib-reorg.html). See commit [d91c0936](https://github.com/tarsqi/ttk/commit/d91c0936aac679bce530bfafcf16da46c35f43a2) for all changes made in this section (the commit contains a few other things too though, just removing or replacing some utilities).

<u>Renamed modules</u>

```
$ python-modernize -wnf libmodernize.fixes.fix_imports_six .
```

This resulted in changes like this

```diff
-import cPickle
+import six.moves.cPickle

-HAVE_FSAs = cPickle.load(openfile("HAVE_FSAs.pickle"))
+HAVE_FSAs = six.moves.cPickle.load(openfile("HAVE_FSAs.pickle"))
```

These were simplified to the following to make it simpler to change to non-six pickle when we are Python3 only.

```diff
-import cPickle
+from six.moves import cPickle
```

<u>Removed modules</u> and the <u>urllib modules</u>

None that I am aware of, did search the code for urllib, nothing there.

<u>The string module</u>

Manually replaced all functions used in this module with string methods, there are about 50-60 of them, mostly in the FSA and wordnet utilities.



### 3.7.  Numbers, dictionaries and comprehensions

See commit [1ae64966](https://github.com/tarsqi/ttk/commit/1ae64966ccc0206e31ba1af822d017c436cd30d0) for changes made in this section.

<u>Numbers</u>

[https://portingguide.readthedocs.io/en/latest/numbers.html](https://portingguide.readthedocs.io/en/latest/numbers.html)

The part on division was already done in section 3.1.

Special methods: there are no occurrences of `__div__`.

Unification of int and long:

```
$ python-modernize -wnf lib2to3.fixes.fix_long .
$ python-modernize -wnf lib2to3.fixes.fix_numliterals .
```

These made no changes.

In Python 2, canonical representations of long integers included the L suffix. For example, repr(2**64) was 18446744073709551616L on most systems. In Python 3, the suffix does not appear. Note that this only affected repr, the string representation (given by str() or print()) had no suffix. The canonical representations are rarely used, except in doctests. Did not check for this, so some doctests may be broken.

Octal literals

```
$ python-modernize -wnf lib2to3.fixes.fix_numliterals .
```

This made no changes.

<u>Dictionaries</u>

[https://portingguide.readthedocs.io/en/latest/dicts.html](https://portingguide.readthedocs.io/en/latest/dicts.html)

```
$ python-modernize -wnf lib2to3.fixes.fix_has_key .
```

This worked, but I also made a manual change to `utilities/wordnet.py`, which had implemented `has_key()` for a class, by adding a `__contains__()` method to the same class.

Key order is not necessarily guaranteed anymore. This issue can be detected by running the code under Python 2 with `PYTHONHASHSEED=random`:

```
$ PYTHONHASHSEED=random python tarsqi.py data/in/simple-xml/tiny.xml out.xml
$ PYTHONHASHSEED=random python testing/run_tests.py
```

This did not unearth any problems.

```
$ python-modernize -wnf libmodernize.fixes.fix_dict_six .
```

Mostly added list() around keys and values. Did manually remove a few. Code should be revisited later.

There were no cases where `iterkeys()` and its friends were used so did not use any six wrappers there.

<u>Comprehensions</u>

[https://portingguide.readthedocs.io/en/latest/comprehensions.html](https://portingguide.readthedocs.io/en/latest/comprehensions.html)

Did not check whether there was any leaking of comprehenzion variables. When running the code in Python 3 name errors may pop up. There could be issues with iteration variables that were set before the comprehension, hard to find, good luck with that, but unlikely to be an issue.

There were no comprehensions over tuples. 



### 3.8.  Iterators

[https://portingguide.readthedocs.io/en/latest/iterators.html](https://portingguide.readthedocs.io/en/latest/iterators.html)

```
$ python-modernize -wnf libmodernize.fixes.fix_map .
$ python-modernize -wnf libmodernize.fixes.fix_filter .
```

This made a fair amount of changes, mostly on third party code (FSA and WordNet). Should review all the uses of map() and filter() and replace them with comprehensions or for loops.

```
$ python-modernize -wnf libmodernize.fixes.fix_zip
```

Just imported zip from six.moves.

```
$ python-modernize -wnf libmodernize.fixes.fix_xrange_six .
```

Imported range from six.moves, added some list functions around results, and removed xrange().



## 4.  Remaining thingies

List of steps still remaining.

- Other core object changes
  - [https://portingguide.readthedocs.io/en/latest/core-obj-misc.html](https://portingguide.readthedocs.io/en/latest/core-obj-misc.html)
- built-in functions
  
  - [https://portingguide.readthedocs.io/en/latest/builtins.html](https://portingguide.readthedocs.io/en/latest/builtins.html)
- comparing and sorting, including rich comparison operators
  - [https://portingguide.readthedocs.io/en/latest/comparisons.html](https://portingguide.readthedocs.io/en/latest/comparisons.html)
  - [http://python3porting.com/preparing.html](http://python3porting.com/preparing.html)
- Other changes
   - [https://portingguide.readthedocs.io/en/latest/etc.html](https://portingguide.readthedocs.io/en/latest/etc.html)

After that we can run `python-modernize` ,`pylint --py3k` and `python -3` when running tarsqi.py and the testing and regression scripts.

Maybe check [http://python3porting.com/stdlib.html#removed-modules](http://python3porting.com/stdlib.html#removed-modules).

Followed by `2to3`.

Remove from future imports and calls to six library.

Also see:

- http://python-future.org/automatic_conversion.html
- http://python-future.org/compatible_idioms.html

