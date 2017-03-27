"""code-stats.py

Print statistics on number of lines of code. Lines of code includes all lines in
.py files, whether they are blank lines, comments, or actual code. Allows rough
comparisons of code size between commits.

Writes a file stats-YYYY-MM-DD-COMMIT.html, where YYYY-MM-DD is the date of the
commit that the git HEAD points at and COMMIT is the 8-character prefix of the
that commit. We get this commit with

   $ git log -n 1 --date-short --pretty=format"%ad %H"

This script should be run from the code directory:

   $ python utilities/code-stats.py

Since this file is not part of early commits, the best way to use it when
getting statistic over old commits is to copy it to the code directory and then
run it from there. There never was a file code-stats.py, so that will not cause
conflicts.

There is a playpen for this on /DATA/misc/ttk. It has several stats files, which
report the following number of lines for the code (excluding the libraries):

            commit  code    lib    3rd
- 2010-09   eb4a1c  16,717  8,118  7,203
- 2013-06   6dc0fd  17,031  8,118  7,207
- 2016-01   b44121  12,261  8,579  7,200

The first date (2010-09) is when the code was imported from subversion (without
the history) and when some redesign efforts just started. The next (2013-06) is
when redesign efforts halted. And the last is a close to current state. The
second column is the commit, the third the number of lines in code files, the
fourth the number of lines in library files and the fifth the number of lines in
3rd-party utilities.

The increased size in the library is due to reformatting evita feature_rules,
the decreased size for the code is all due to cleanup and simplification.

"""


import os, sys, subprocess

command = ['git', 'log', '-n', '1', '--date=short', '--pretty=format:"%ad %H"']
result = subprocess.Popen(command, stdout=subprocess.PIPE).communicate()[0]
date = result[1:11]
commit = result[12:20]

STATS = {
    '3rd-party-utils': [],
    'deprecated': [],
    'library': [],
    'code': []
}

STATS_FILE = open("stats-%s-%s.html" % (date, commit), 'w')

UTILS = {
    './utilities/FSA.py': True,
    './utilities/FSA-org.py': True,
    './utilities/wordnet.py': True,
    './utilities/wntools.py': True,
    './components/preprocessing/treetaggerwrapper.py': True
}


def get_type(fname):
    if UTILS.get(fname):
        return '3rd-party-utils'
    elif fname.startswith('./deprecated'):
        return 'deprecated'
    elif fname.startswith('./library'):
        return 'library'
    else:
        return 'code'

for root, dirs, files in os.walk("."):
    files = [f for f in files if f.endswith('.py')]
    for name in files:
        fname = os.path.join(root, name)
        fh = open(fname)
        lines = len(fh.readlines())
        STATS[get_type(fname)].append([fname, lines])

STATS_FILE.write("<table cellspacing=0 cellpadding=3 border=1>\n")
for filetype, values in STATS.items():
    STATS_FILE.write("<tr><td colspan=3><b>%s</b>\n" % filetype)
    total_lines = 0
    for (fname, lines) in values:
        total_lines += lines
        STATS_FILE.write("<tr><td>%s<td align=right>%s\n" % (fname, lines))
    STATS_FILE.write("<tr><td>&nbsp;<td align=right><b>%s</b>\n" % (total_lines))
STATS_FILE.write("</table>\n")
