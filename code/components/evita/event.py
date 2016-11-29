"""event.py

The Event class here is used by Evita when creating a new event by
Chunk._processEventInChunk() or AdjectiveToken._processEventInToken().

"""

from library.main import LIBRARY
from library.tarsqi_constants import EVITA


class Event:

    """Instances of this class are created by Evita when it finds a new
    event. Instances have a short life because all that they are used for is to
    be added to the TarsqiDocument as a Tag instance.

    Instance variables:
      tokens  -  a list of Tokens or AdjectiveTokens
      attrs   -  the TimeML attributes of the event

    The eid and eiid identifiers are not set by this class, they are added later
    when the TarsqiTree adds the event to the TarsqiDocument. Also note that
    the nf_morph is value is added to the POS attribute.

    """

    def __init__(self, feats):
        """Initialize from an instance of a subclass of ChunkFeatures. Creates
        the list of tokens for the event from just the head of the chunk because
        currently Evita only recognizes one-token events (in line with the old
        TimeML specifications), the list is a hook for adding multi-token events
        later. Modality and polarity are not added if they have the default
        values."""
        self.tokens = [feats.head]
        self.attrs = { LIBRARY.timeml.EID: None, LIBRARY.timeml.EIID: None }
        self.attrs[LIBRARY.timeml.ORIGIN] = EVITA
        self.attrs[LIBRARY.timeml.CLASS] = feats.evClass
        self.attrs[LIBRARY.timeml.TENSE] = feats.tense
        self.attrs[LIBRARY.timeml.ASPECT] = feats.aspect
        self.attrs[LIBRARY.timeml.POS] = feats.nf_morph
        if feats.modality != 'NONE':
            self.attrs[LIBRARY.timeml.MODALITY] = feats.modality
        if feats.polarity != 'POS':
            self.attrs[LIBRARY.timeml.POLARITY] = "NEG"
