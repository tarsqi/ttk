"""Classes and methods for converting formats in the TARSQI preprocessing pipeline
    
"""


def normalizeXML(word):

    """Returns a string with occurrences of '&', '<' and '>' replaced
    with with '&amp;', '&lt;' and '&gt;' respectively.

    Arguments
       word - a string"""

    word = word.replace('&', '&amp;')
    word = word.replace('<', '&lt;')
    word = word.replace('>', '&gt;')
    return word


def normalizePOS(pos):
    
    if pos == 'SENT':
        pos ='.'
    elif pos[0] == 'V':
        if pos[1] in ['V', 'H']:
            if len(pos) > 2:
                rest = pos[2:]
            else: rest = ''
            pos = 'VB' + rest
    elif pos == "NP":
        pos = "NNP"
    # new version of treetagger changed the tag for 'that'
    elif pos == 'IN/that':
        pos = 'IN'
    return pos
        

def verticalize_text(text):

    """Returns the text in a one-token-per-line format. Adds an <s> at
    the beginning of each line in the input text. Intended to take
    tokenized text and prepare it for the TreeTagger (which does not
    recognize </s> tags."""

    result_string = ''
    for line in text.split('\n'):
        if line == '':
            continue
        lineList = line.split()
        result_string += '<s>\n'
        for item in lineList:
            result_string += item+"\n"
    return result_string
