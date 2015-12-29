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

    def t(self, sentence, o1, o2):
        message = "%s[%s]%s" % (sentence[:o1], sentence[o1:o2], sentence[o2:])
        self.assertTrue(check(self.pipeline, sentence, 'TIMEX3', o1, o2), message)

    def test_01(self): self.t("It is June 5th.", 6, 14)
    def test_02(self): self.t("John sleeps today.", 12, 17)


class EvitaTest(unittest.TestCase):
    """A couple of tests just to confirm that EVENT tags are actually added to a
    couple of simple sentences. Tries to hit the various cases (nominal,
    adjectival and different kinds of verbs). A test needs a name (which does
    not need to be unique), a string to run on and the two offsets of the
    event."""

    @classmethod
    def setUpClass(cls):
        cls.pipeline = 'PREPROCESSOR,EVITA'

    def t(self, name, s, o1, o2, tag=True, feature=None):
        """If tag=True we test for presence of the tag, it tag=False then we test for
        absence of the tag, feature=None is there as a place holder for when we
        start testing features like class, modality and polarity."""
        message = "%s - %s[%s]%s" % (name, s[:o1], s[o1:o2], s[o2:])
        message += ' - FALSE NEGATIVE' if tag else ' - FALSE POSITIVE'
        result = check(self.pipeline, s, 'EVENT', o1, o2)
        self.assertTrue(result, message) if tag else self.assertFalse(result, message)

    def test_01a(self): self.t('NOUN', "The war is over.", 4, 7)
    def test_01b(self): self.t('NOUN', "The man is old.", 4, 7, tag=False)
    def test_02a(self): self.t('VERB', "Fido barks.", 5, 10)
    def test_02b(self): self.t('VERB', "John sleeps today.", 5, 11)
    # need case for MODAL
    def test_03a(self): self.t('BE-ADJ', "The door is open.", 12, 16)
    def test_04a(self): self.t('BE-NOM', "There was a war.", 12, 15)
    def test_04b(self): self.t('BE-NOM', "There was a war.", 6, 9, tag=False)
    def test_04b(self): self.t('BE-NOM', "There was a man.", 6, 9, tag=False)
    def test_04b(self): self.t('BE-NOM', "There was a man.", 12, 15, tag=False)
    def test_05a(self): self.t('BECOME', "Women have become the sole support of their families.", 11, 17)
    def test_05b(self): self.t('BECOME-ADJ', "Women have become alarmed.", 11, 17)
    def test_05c(self): self.t('BECOME-ADJ', "Women have become alarmed.", 18, 25)
    def test_06a(self): self.t('CONTINUE', "The earnings continued to be excellent.", 13, 22)
    def test_06b(self): self.t('CONTINUE-ADJ', "The earnings continued to be excellent.", 13, 22)
    def test_06c(self): self.t('CONTINUE-ADJ', "The economic embargo on materials continued unabated.", 34, 43)
    def test_06d(self): self.t('CONTINUE-ADJ', "The economic embargo on materials continued unabated.", 44, 52)
    def test_07a(self): self.t('DO', "You can do that.", 8, 10)
    # need case for DO-AUX
    def test_08a(self): self.t('GOING', "The fundamental change the industry is going through.", 39, 44)
    def test_08b(self): self.t('GOING-TO', "We are going to maintain our forces in the region.", 7, 12, tag=False)
    def test_08b(self): self.t('GOING-TO', "We are going to maintain our forces in the region.", 16, 24) # FUTURE
    def test_09a(self): self.t('HAVE-1', "All Arabs would have to move behind Iraq.", 16, 20, tag=False)
    def test_09b(self): self.t('HAVE-1', "All Arabs would have to move behind Iraq.", 24, 28)
    def test_09c(self): self.t('HAVE-2', "The Iraqi leadership did not have a rational approach.", 29, 33)
    def test_10a(self): self.t('KEEP', "The stocks they keep on hand to sell investors.", 16, 20) # ASPECTUAL
    def test_10b(self): self.t('KEEP', "They intend to keep interest rates unchanged.", 15, 19) # ASPECTUAL
    def test_10c(self): self.t('KEEP', "They intend to keep interest rates unchanged.", 35, 44) # STATE


class SlinketTest(unittest.TestCase):
    """A couple of tests to confirm that an SLINK was added with the correct
    relTypes and event instances on the right offsets."""

    @classmethod
    def setUpClass(cls):
        cls.pipeline = 'PREPROCESSOR,EVITA,SLINKET'

    def t(self, s, name, e1, e2, reltype, tag=True, feature=None):
        # the feature=None is there as a place holder for when we start testing
        # features like class, modality and polarity
        result = check_link(self.pipeline, s, 'SLINK', e1, e2, reltype)
        self.assertTrue(result) if tag else self.assertFalse(result)

    def test_01a(self): self.t("John saw the miners build a fence.",
                               'SLINK', (5,8), (20,25), 'EVIDENTIAL')
    def test_01b(self): self.t("He said the dogs slept.",
                               'SLINK', (3,7), (17,22), 'EVIDENTIAL')
    def test_02a(self): self.t("He wanted to walk.",
                               'SLINK', (3,9), (13,17), 'MODAL')


def check(pipeline, sentence, tag, o1, o2):
    """Return True if sentence has tag between offsets o1 and o2."""
    options = [('--pipeline', pipeline), ('--loglevel', '1')]
    td = tarsqi.process_string(sentence, options)
    tags = td.elements[0].tarsqi_tags.find_tags(tag)
    for t in tags:
        if t.begin == o1 and t.end == o2:
            return True
    return False

def check_link(pipeline, sentence, tagname, e1_offsets, e2_offsets, reltype):
    """Returns True if there is a link tagname that ..."""
    options = [('--pipeline', pipeline), ('--loglevel', '1')]
    td = tarsqi.process_string(sentence, options)
    link_tags = td.elements[0].tarsqi_tags.find_tags(tagname)
    event_tags = td.elements[0].tarsqi_tags.find_tags('EVENT')
    if not link_tags:
        return False
    for link_tag in link_tags:
        eiid1 = link_tag.attrs['eventInstanceID']
        eiid2 = link_tag.attrs['subordinatedEventInstance']
        relType = link_tag.attrs['relType']
        e1 = select_event(eiid1, event_tags)
        e2 = select_event(eiid2, event_tags)        
        return (e1.begin == e1_offsets[0] and e1.end == e1_offsets[1]
                and e2.begin == e2_offsets[0] and e2.end == e2_offsets[1]
                and relType == reltype)

def select_event(eiid, event_tags):
    for event_tag in event_tags:
        if event_tag.attrs['eiid'] == eiid:
            return event_tag
    return None

            
def test_all():
    test_gutime()
    test_evita()
    test_slinket()

def test_gutime():
    print "\n%s\nGUTIME TESTS\n%s" % ('-'*70, '-'*70)
    suite = unittest.TestLoader().loadTestsFromTestCase(GUTimeTest)
    unittest.TextTestRunner(verbosity=2).run(suite)
    
def test_evita():
    print "\n%s\nEVITA TESTS\n%s" % ('-'*70, '-'*70)
    suite = unittest.TestLoader().loadTestsFromTestCase(EvitaTest)
    unittest.TextTestRunner(verbosity=2).run(suite)

def test_slinket():
    print "\n%s\nSLINKET TESTS\n%s" % ('-'*70, '-'*70)
    suite = unittest.TestLoader().loadTestsFromTestCase(SlinketTest)
    unittest.TextTestRunner(verbosity=2).run(suite)


if __name__ == '__main__':

    # a dummy run just to get the tagger messages out of the way
    tarsqi.process_string("Fido barks.", [('--pipeline', 'PREPROCESSOR')])

    opts, args = getopt.getopt(sys.argv[1:], '', ['evita', 'gutime', 'slinket'])
    if not opts:
        test_all()
    else:
        for opt, val in opts:
            if opt == '--evita': test_evita()
            if opt == '--gutime': test_gutime()
            if opt == '--slinket': test_slinket()
