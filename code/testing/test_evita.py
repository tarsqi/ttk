import os
import unittest

from testing.common import load_mappings


MAPPINGS_DIR = os.path.join(os.getcwd(), 'testing', 'cases', 'evita')

MAPPINGS = {}


if not MAPPINGS:
    MAPPINGS = load_mappings(MAPPINGS_DIR + os.sep + 'evita-cases.txt')


class TestEvita(unittest.TestCase):

    #def test_001(self): self.run_test('001')
    #def test_002(self): self.run_test('002')
    
    def run_test(self, id):
        test_desciption = MAPPINGS[id]['description']
        test_input = MAPPINGS[id]['input']
        test_output = MAPPINGS[id]['output']
        self.assertEqual(test_input, test_output, test_description)




