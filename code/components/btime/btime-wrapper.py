"""

An example wrapper that shows how BTime will be called by the Tarsqi Toolkit.

BTime will be handed a list of instances of Token or some similar class. Instances of this
class will at least have methods text(), tag(), begin(), end() and __unicode__(). The
begin and end offsets are a little but faked here because they are not relative to the
position in the text source but relative to a normalized representation that is derived
from the tokenization.

It should be easy to insert BTime given that Alex's code uses __unicode__() to get to the
text. The method to edit below is parse_sentence().


Usage:

   % python btime-wrapper.py FILENAME

   FILENAME is a file with tokenized and tagged text, whose content should like like
   
      In/IN Singapore/NNP ,/, stocks/NNS hit/VBD a/DT five/CD year/NN low/JJ ./.
      In/IN the/DT Philippines/NPS ,/, a/DT four/CD year/NN low/JJ ./.

"""


import sys, codecs


def parse_file(filename):

    f = codecs.open(filename, encoding='utf-8')
    lexid = 0
    for line in f:
        tokens = line.split()
        sentence = []
        pos = 0
        for token in tokens:
            text, tag = token.split('/', 2)
            lexid += 1
            p1 = pos
            p2 = pos + len(text)
            t = Token(text, tag, lexid, p1, p2)
            #print t
            pos += len(text) + 1
            sentence.append(t)
        parse_sentence(sentence)


def parse_sentence(sentence):
    """This is  here BTime gets folded in."""
    print "processing \"%s\"" % ' '.join([t.text for t in sentence])



class Token(object):

    def __init__(self, text, tag, lexid, p1, p2):
        self.text = text
        self.tag = tag
        self.lexid = lexid
        self.begin = p1
        self.end = p2

    def __unicode__(self):
        return self.text

    def __str__(self):
        return "<Token id=%d begin=%d end=%d tag=\"%s\" text=\"%s\">" % \
            (self.lexid, self.begin, self.end, self.tag, self.text)


    
if __name__ == '__main__':

    filename = sys.argv[1]
    parse_file(filename)
