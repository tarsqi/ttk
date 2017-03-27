"""

Module to access list of nominals havested from WordNet.

"""

from library import forms
import utilities.binsearch as binsearch
import utilities.logger as logger


# Open dbm's with information about nominal events. If that does not work, open
# all corresponding text files, these are a fallback in case the dbm's are not
# supported or not available
try:
    # these dictionaries are not under git control or bundled with Tarsqi, but
    # they can be generated with library/evita/build_event_nominals2.py
    wnPrimSenseIsEvent_DBM = anydbm.open(forms.wnPrimSenseIsEvent_DBM,'r')
    wnAllSensesAreEvents_DBM = anydbm.open(forms.wnAllSensesAreEvents_DBM,'r')
    wnSomeSensesAreEvents_DBM = anydbm.open(forms.wnSomeSensesAreEvents_DBM,'r')
    DBM_FILES_OPENED = True
except:
    wnPrimSenseIsEvent_TXT = open(forms.wnPrimSenseIsEvent_TXT,'r')
    wnAllSensesAreEvents_TXT = open(forms.wnAllSensesAreEvents_TXT,'r')
    wnSomeSensesAreEvents_TXT = open(forms.wnSomeSensesAreEvents_TXT,'r')
    DBM_FILES_OPENED = False
# TODO: these should not be specified in forms but somewhere in the evita
# library (similar to how Slinket does it)


## code for lookup in WordNet

def primarySenseIsEvent(lemma):
    """Determine whether primary WN sense is an event."""
    if DBM_FILES_OPENED:
        return _lookupLemmaInDBM(lemma, wnPrimSenseIsEvent_DBM)
    return _lookupLemmaInTXT(lemma, wnPrimSenseIsEvent_TXT)

def allSensesAreEvents(lemma):
    """Determine whether all WN senses are events."""
    if DBM_FILES_OPENED:
        return _lookupLemmaInDBM(lemma, wnAllSensesAreEvents_DBM)
    return _lookupLemmaInTXT(lemma, wnAllSensesAreEvents_TXT)

def someSensesAreEvents(lemma):
    """Determine whether some WN senses are events."""
    if DBM_FILES_OPENED:
        return _lookupLemmaInDBM(lemma, wnSomeSensesAreEvents_DBM)
    return _lookupLemmaInTXT(lemma, wnSomeSensesAreEvents_TXT)

def _lookupLemmaInDBM(lemma, dbm):
    """Look up lemma in database."""
    # has_key on dbm returns 0 or 1, hence the if-then-else
    return True if dbm.has_key(lemma) else False

def _lookupLemmaInTXT(lemma, fh):
    """Look up lemma in text file."""
    line = binsearch.binarySearchFile(fh, lemma, "\n")
    return True if line else False
