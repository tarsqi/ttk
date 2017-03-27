import os, sys


def elements_file():
    return os.path.join(os.environ['TTK_ROOT'], 'components', 'simpletime', 'elements.txt')

def rules_file():
    return os.path.join(os.environ['TTK_ROOT'], 'components', 'simpletime', 'rules.txt')


def load_types():
    type_order = []
    type_index = {}
    current = None
    for line in open(elements_file()):
        line = line.strip()
        if line.startswith('#'):
            continue
        elif not line:
            if current is not None:
                type_index[current.name] = current
            current = None
        else:
            fields = line.split()
            if fields[0] == 'ELEMENT':
                type_order.append(fields[1])
                if fields[2] == 'LIST':
                    current = WordList(fields[1])
                    for string in fields[3:]:
                        current.add(string)
                if fields[2] == 'EXP':
                    current = RegularExpression(fields[1])
                    for string in fields[3:]:
                        current.add(string)
            else:
                for string in fields:
                    current.add(string)
    if current is not None:
        type_index[current.name] = current
    return type_order, type_index


def load_rules():
    rules = []
    for line in open(rules_file()):
        line = line.strip()
        if line.startswith('#'):
            continue
        elif not line:
            continue
        else:
            lhs, rhs = [s.strip() for s in line.split('=',1)]
            rhs = rhs.split()
            rules.append(CombinationRule(lhs, rhs))
    return rules

class Date:
    name = 'Date'


class TimexElement:

    def is_word_list(self):
        return False

    def is_regular_expression(self):
        return False


class WordList(TimexElement):

    def __init__(self, name):
        self.name = name
        self.words = []
        self.idx = set()

    def add(self, string):
        self.words.append(string)
        self.idx.add(string)

    def is_word_list(self):
        return True

    def match(self, word):
        pass
        
    def pp(self):
        print "%s = %s" % (self.name, ' '.join(list(self.words)))


class RegularExpression(TimexElement):

    def __init__(self, name):
        self.name = name
        self.regexp = None

    def add(self, string):
        self.regexp = string

    def match(self, word):
        pass
        
    def is_regular_expression(self):
        return True

    def pp(self):
        print "%s = %s" % (self.name, self.regexp)


class CombinationRule:

    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def pp(self):
        print "%s --> %s" % (self.lhs, ' '.join(self.rhs))


def get_class(class_name):
    print classname, '=',
    classobj = vars(sys.modules[__name__])[classname]
    return classobj


class SimpleTime():

    def __init__(self):
        type_order, type_index = load_types()
        self.type_order = type_order
        self.type_index = type_index
        self.rules = load_rules()

    def show_type(self, classname):
        self.type_index[classname].pp()
        
    def show_rules(self):
        for rule in self.rules:
            rule.pp()

    def extract_times(self, text):
        print 'On <TIMEX3 type="DATE" val="2012-04-25>April 25th, 2012</TIMEX3>, they approached the border.'


if __name__ == '__main__':

    # this is needed if we cannot rely on the TTK_ROOT variable
    scriptPath = os.path.abspath(__file__)
    scriptDir = os.path.dirname(scriptPath)
    tarsqiDir = os.path.abspath(os.path.join(scriptDir, '..', '..'))
    os.environ['TTK_ROOT'] = tarsqiDir
    
    st = SimpleTime()
    st.show_type('Month')
    st.show_type('Year')
    st.show_rules()
