
# Porting to Python 3

This document has some notes on the effort to get a Python 3 version of TTK. Originally, the goal was to get a few steps along the way without any impact to TTK users, that is, no extra installations, not even something as simple as `pip install future` or `pip install builtins`. The goal was also to eventually change the code so that it supports both Python 2.7 and Python 3.5 and up.

This was all dropped. The goal is to get a Python3 version in TTK version 3.0.0. Period. Probably version 3.6. This might require extra installation, fine. And version 2.7 will not be supported anymore apart from minimal bug fixes on version 2.2.0.




### 1. Process

For now:

- Started branch `79-python3`.

- Following the steps in [https://portingguide.readthedocs.io/en/latest/process.html](https://portingguide.readthedocs.io/en/latest/process.html)

  - After each step, review the changes, do not yet make any manual edits
  - After one or more steps, run the tests and if they pass put all changes in the git staging area.
  - Try to isolate automatic amd manual changes in separate commits. The only exception is that this file may be updated in a commit alongside automatic changes.

- Also looking at [http://python3porting.com/preparing.html](http://python3porting.com/preparing.html) to do those preparatory changes that allow you to still run under Python2 (division, strings, new classes, etcetera). There obviously is major overlap between this one and the previous one.

- Using

  -  `python-modernize` to give hints on the idioms to change.
    - probably using individual fixers
  -  `pylint --py3k` for more hints on Python3 compatibility.

In the following, each section corresponds to one or more commits on the `79-python3` branch.



### 2. Initial syntax changes

These changes are based on https://portingguide.readthedocs.io/en/latest/syntax.html.

<u>Syntax Change 1: Get rid of tabs</u>

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

<u>Syntax Change 2: Tuple Unpacking in Parameter Lists</u>

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

<u>Syntax Change 3: Backticks</u>

```
$ python-modernize -wnf lib2to3.fixes.fix_repr .
```

No problems.

<u>Syntax Changes: Others</u>

There was no need to remove the inequality operator `<>` and there were no assignments to True or False. Other syntax changes are done in later steps. Want to find out why.

The changes in this section are in commit [94b2bce5](https://github.com/tarsqi/ttk/commit/94b2bce5e5b68e688d4d385bcb2b022b4f1e7093).

### 2. More preparatory changes

Based on [http://python3porting.com/preparing.html](http://python3porting.com/preparing.html). These are similar to the above in that they allow the code to still run on Python 2.7.

<u>Division of integers</u>

Using // when we really want to have integers as the result, using / in other cases. Sometimes using `from __future__ import division` and removing explicit conversions into floats.

