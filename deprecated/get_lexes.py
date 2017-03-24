"""

Standalone utility script to extract all the tokens from a file and print them space
separated using one sentence per line. Files are XML files that need to contain <s> and
<lex> tags.

USAGE:

    % python get_lexes.py INFILE OUTFILE
    % python get_lexes.py INDIR OUTDIR

Note that in the first case INFILE has to exist and outfile not. In the second case, INDIR
and OUTDIR have to be directories, existing files in OUTDIR may be overwritten.

"""


import sys, os

from xml.dom.minidom import parse


def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)


def get_lexes(infile, outfile):

    try:
        dom = parse(infile)
    except:
        "Warning in XML parsing, skipping %s" % infile
        return
    fh = file(outfile, 'w')
    sentences = dom.getElementsByTagName("s")
    for sentence in sentences:
        tokens = []
        lexes = sentence.getElementsByTagName("lex")
        for lex in lexes:
            tokens.append(getText(lex.childNodes))
        fh.write(' '.join(tokens).encode('utf-8') + "\n")
        
        
if __name__ == '__main__':

    IN = sys.argv[1]
    OUT = sys.argv[2]
    if os.path.isfile(IN) and not os.path.exists(OUT):
        get_lexes(IN, OUT)
    elif os.path.isdir(IN) and os.path.isdir(OUT):
        for filename in os.listdir(IN):
            infile = IN + os.sep + filename
            outfile = OUT + os.sep + filename
            if outfile[-3:] == 'xml':
                outfile = outfile[:-3] + 'txt'
            print outfile
            get_lexes(infile, outfile)
