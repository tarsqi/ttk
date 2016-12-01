"""Code to apply Evita feature rules

Contains the code for matching token sequences against feature rules. The
feature rules are defined in library.evita.patterns.feature_rules.FEATURE_RULES
and are used by the VChunkFeatures class in Evita.

"""


class FeatureRule:

    """Objects of this class contain a chunk and a feature rule and are tasked
    with matching the rule to the chunk."""

    def __init__(self, rule, chunk):
        """Initialize the rule, with name, left-hand side and right-hand side, and add
        the chunk it will apply to."""
        self.rule = rule
        self.rule_name = rule[0]
        self.rule_lhs = rule[1:-1]
        self.rule_rhs = rule[-1]
        self.chunk = chunk

    def __str__(self):
        return "<FeatureRule %s>\n" % self.rule_name \
            + "   LHS: %s\n" % self.rule_lhs \
            + "   RHS: %s\n" % str(self.rule_rhs)

    def match(self):
        """Match the rule to the chunk. Return the right-hand side of the rule if it was
        succesfull and return False otherwise."""
        rule_idx = 0
        chunk_idx = 0
        for i in range(len(self.rule_lhs)/2):
            if not (self._matchWord(self.rule_lhs[rule_idx], chunk_idx) and
                    self._matchPos(self.rule_lhs[rule_idx+1], chunk_idx)):
                return False
            rule_idx += 2
            chunk_idx += 1
        return self.rule_rhs

    def _matchWord(self, ruleInfo, i):
        """Match the rule info to the string of the token at index i. If there
        is no ruleInfo, then consider the rule matched."""
        return self._checkItem(self.chunk[i].getText(), ruleInfo)

    def _matchPos(self, ruleInfo, i):
        """Match the rule info to the pos of the token at index i. If there
        is no ruleInfo, then consider the rule matched."""
        return self._checkItem(self.chunk[i].pos, ruleInfo)

    def _checkItem(self, chunk_element, ruleInfo):
        """Check whether the chunk element matches the rule."""
        if not ruleInfo:
            return True
        operator = " " + ruleInfo[0].strip() + " "
        rule_element = ruleInfo[1]
        return eval('chunk_element' + operator + 'rule_element')
