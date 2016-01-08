"""event.py

The Event class here is used by Evita when creating a new event by
Chunk._processEventInChunk() or AdjectiveToken._processEventInToken().

"""

from library.timeMLspec import EID, EIID, CLASS
from library.timeMLspec import TENSE, ASPECT, POS, MODALITY, POLARITY


class Event:

    """Instances of this class are created by Evita when it finds a new
    event. Instances have a short life because all that they are used for is to
    be added to the TarsqiDocElement as a Tag instance.

    Instance variables:
      tokens  -  a list of Tokens or AdjectiveTokens
      attrs   -  the TimeML attributes of the event

    The eid and eiid identifiers are not set by this class, they are added later
    when the TarsqiTree adds the event to the TarsqiDocElement. Also note that
    the nf_morph is value is added to the POS attribute.

    """

    def __init__(self, gramCh):
        """Initialize from a GramNChunk, GramVChunk or GramACHunk. Creates the list of
        the head of the GramChunk and creates the tokens list with the head as
        the sole element. Currently Evita only recocgnizes one-token events (in
        line with the old TimeML specifications), the list is a hook for adding
        multi-token events. Modality and polarity are not added if they have the
        default values."""
        self.tokens = [gramCh.head]
        self.attrs = { EID: None, EIID: None }
        self.attrs[CLASS] = gramCh.evClass
        self.attrs[TENSE] = gramCh.tense
        self.attrs[ASPECT] = gramCh.aspect
        self.attrs[POS] = gramCh.nf_morph
        if gramCh.modality != 'NONE':
            self.attrs[MODALITY] = gramCh.modality
        if gramCh.polarity != 'POS':
            self.attrs[POLARITY] = "NEG"
