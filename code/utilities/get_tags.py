"""

Takes a TimeML file with at least s and lex tags, and writes tokenenized and tagged
output, using one line per sentence.

Code like this should be added somewhere else, probably to some module in docmodel.

"""


import os, glob

from xml.dom import minidom


INDIR = "data/out/Timebank"
OUTDIR = "data/out/Timebank2"

def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)


for infile in glob.glob( os.path.join(INDIR, '*.xml') ):
    
    print infile
    
    outfile = os.path.basename(infile)[:-3] + 'txt'
    fh = open( os.path.join(OUTDIR, outfile ), 'w')
    dom = minidom.parse(infile) 
    sentences = dom.getElementsByTagName("s")

    for sentence in sentences:
        tokens = sentence.getElementsByTagName("lex")
        toks = ["%s/%s" % (getText(t.childNodes), t.getAttribute('pos')) for t in tokens]
        fh.write(" ".join(toks) + "\n")
    
