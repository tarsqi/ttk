"""ttk_unittests.py

Simple unit tests that ping the system in various ways. All current test just
confirm that some component adds a tag at the proper spot in a sentence.

They are actually not really unit tests because they test fairly high-level
functionality like adding particular tags, but it was convenient to use the
unittest framework.

These test are not intended for extensive testing of coverage.

Usage:

   $ python ttk_unittests.py OPTIONS*

The following options are available:

   --gutime  run the GUTime tests
   --evita   run the Evita tests

Without options all test will run.

Examples:

   $ python test.py --evita
   $ python test.py --gutime --evita

"""

import sys, unittest, getopt

import path
import tarsqi


class GUTimeTest(unittest.TestCase):
    """A couple of tests just to confirm that TIMEX3 tags are actually added to a
    couple of simple sentences."""

    @classmethod
    def setUpClass(cls):
        cls.pipeline = 'PREPROCESSOR,GUTIME'

    def run_test(self, sentence, o1, o2):
        message = "%s[%s]%s" % (sentence[:o1], sentence[o1:o2], sentence[o2:])
        self.assertTrue(check(self.pipeline, sentence, 'TIMEX3', o1, o2), message)

    def test_01(self): self.run_test("It is June 5th.", 6, 14)
    def test_02(self): self.run_test("John sleeps today.", 12, 17)


class EvitaTest(unittest.TestCase):
    """A couple of tests just to confirm that EVENT tags are actually added to a
    couple of simple sentences."""

    @classmethod
    def setUpClass(cls):
        cls.pipeline = 'PREPROCESSOR,EVITA'

    def run_test(self, sentence, o1, o2):
        message = "%s[%s]%s" % (sentence[:o1], sentence[o1:o2], sentence[o2:])
        self.assertTrue(check(self.pipeline, sentence, 'EVENT', o1, o2), message)

    def test_01(self): self.run_test("Fido barks.", 5, 10)
    def test_02(self): self.run_test("John sleeps today.", 5, 11)
    def test_03(self): self.run_test("The door is open.", 12, 16)
    def test_04(self): self.run_test("The war is over.", 4, 7)


def check(pipeline, sentence, tag, o1, o2):
    """Return True if sentence has tag between offsets o1 and o2."""
    options = [('--pipeline', pipeline), ('--loglevel', '1')]
    td = tarsqi.process_string(sentence, options)
    tags = td.elements[0].tarsqi_tags.find_tags(tag)
    for t in tags:
        if t.begin == o1 and t.end == o2:
            return True
    return False

def test_all():
    test_gutime()
    test_evita()

def test_gutime():
    print "\n%s\nGUTIME TESTS\n%s" % ('-'*70, '-'*70)
    suite = unittest.TestLoader().loadTestsFromTestCase(GUTimeTest)
    unittest.TextTestRunner(verbosity=2).run(suite)
    
def test_evita():
    print "\n%s\nEVITA TESTS\n%s" % ('-'*70, '-'*70)
    suite = unittest.TestLoader().loadTestsFromTestCase(EvitaTest)
    unittest.TextTestRunner(verbosity=2).run(suite)


if __name__ == '__main__':

    # a dummy run just to get the tagger messages out of the way
    tarsqi.process_string("Fido barks.", [('--pipeline', 'PREPROCESSOR')])

    opts, args = getopt.getopt(sys.argv[1:], '', ['evita', 'gutime'])
    if not opts:
        test_all()
    else:
        for opt, val in opts:
            if opt == '--evita': test_evita()
            if opt == '--gutime': test_gutime()

