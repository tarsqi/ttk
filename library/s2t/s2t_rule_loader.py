from __future__ import absolute_import
from __future__ import print_function
import os
import re
from io import open

TTK_ROOT = os.environ['TTK_ROOT']

S2T_RULES = os.path.join(TTK_ROOT, 'library', 's2t', 's2t_rules.txt')

re_ruleNum = re.compile('ruleNum=(\d+)')
re_event = re.compile('(event*)=(.*)')
re_subevent = re.compile('(subevent*)=(.*)')
re_reltype = re.compile('(.*)=(.*)')
re_attribute = re.compile('(.*)=(.*)')


class S2TRule(object):

    """Implements the S2T rule object. An S2T rule consists of an ID
    number and a set of conditions including:
    
       -- Optional Conditions:  tense, aspect, reltype.
       -- Mandatory Condition:  relation (the reltype for the new TLINK)."""

    # TODO: that is NOT a mandatory condition, change this so we talk about lhs
    # and rhs or something like that

    def __init__(self, ruleNum):
        self.id = "%s" % (ruleNum)
        self.attrs = {}

    def set_attribute(self, attr, val):
        self.attrs[attr] = val

    def get_attribute(self, attr):
        self.attrs.get(attr)

    def __str__(self):
        return '<S2TRule ' + self.id + '>'
    
    def pp(self):
        print("<S2TRule %s>" % self.id)
        for attr, val in self.attrs.items():
            print("  %s=\"%s\"" % (attr, val))


def read_rules():

    """Read and return a list of all the rules in S2T_RULES."""

    rules = []
    current_rule = None
    file = open(S2T_RULES, 'r')

    for line in file.readlines():
        # skip comments and empty lines
        line = line.strip()
        if line.startswith('#') or line == '':
            continue
        # find rule header
        match = re_ruleNum.search(line)
        if match:
            if current_rule:
                # store previous rule and reset it
                rules.append(current_rule)
                current_rule = None
            (ruleNum) = match.group(1)
            current_rule = S2TRule(ruleNum)
            continue
        # find attributes
        match = re_event.search(line)
        if match:
            (att, val) = match.group(1,2)
            current_rule.set_attribute(att.strip(), val.strip())
            continue
        match = re_subevent.search(line)
        if match:
            (att, val) = match.group(1,2)
            current_rule.set_attribute(att.strip(), val.strip())
            continue
        match = re_reltype.search(line)
        if match:
            (att, val) = match.group(1,2)
            current_rule.set_attribute(att.strip(), val.strip())
            continue

    # do not forget the very last rule
    if current_rule:
        rules.append(current_rule)

    #for rule in rules: rule.pp()
    
    return rules

