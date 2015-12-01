"""

Contains the code for matching token sequences against feature rules. The fuetur
rules are defined in library.evita.patterns.feature_rules.FEATURE_RULES and are
used by the GramVChunk class in Evita.

"""

import string

class FeatureRule:

    """Objects of this class contain a chunk and a feature rule and are tasked
    with matching the rule to the chunk."""

    def __init__(self, rule, chunk): 
        self.rule = rule
        self.rule_name = rule[0]
        self.rule_rhs = rule[-1]
        self.rule_lhs = rule[1:-1]
        self.chunk = chunk

    def __str__(self):
        return "<FeatureRule %s>\n" % self.rule_name \
            + "   LHS: %s\n" % self.rule_lhs \
            + "   RHS: %s\n" % str(self.rule_rhs)

    def match(self):
        rule_idx = 0
        chunk_idx = 0
        for i in range(len(self.rule_lhs)/2):
            if not (self.matchWord(self.rule_lhs[rule_idx], chunk_idx) and
                    self.matchPos(self.rule_lhs[rule_idx+1], chunk_idx)):
                return False
            rule_idx += 2
            chunk_idx += 1
        return self.rule_rhs

    def matchWord(self, ruleInfo, i):
        """Match the rule info to the string of the token at index i. If there
        is no ruleInfo, then consider the rule matched."""
        if not ruleInfo: return True
        else: return self.checkItem(self.chunk[i].getText(), ruleInfo)

    def matchPos(self, ruleInfo, i):
        """Match the rule info to the pos of the token at index i. If there
        is no ruleInfo, then consider the rule matched."""
        if not ruleInfo: return True
        else: return self.checkItem(self.chunk[i].pos, ruleInfo)

    def checkItem(self, elem, tuple):
        op = " " + string.strip(tuple[0]) + " "
        elem2 = tuple[1]
        if op == " == " and elem2 == 'None':
            if not elem: return 1
            else: return 0
        elif op == " != " and elem2 == 'None':
            if not elem: return 0
            else: return 1
        else: return eval(string.lower('elem') + op + 'elem2')



