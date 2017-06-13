"""event.py

The Event class here is used by Evita when creating a new event by
Chunk._processEventInChunk() or AdjectiveToken._processEventInToken().

"""

from library.main import LIBRARY
from library.tarsqi_constants import EVITA

EID = LIBRARY.timeml.EID
EIID = LIBRARY.timeml.EIID
ORIGIN = LIBRARY.timeml.ORIGIN
CLASS = LIBRARY.timeml.CLASS
TENSE = LIBRARY.timeml.TENSE
ASPECT = LIBRARY.timeml.ASPECT
POS = LIBRARY.timeml.POS
MODALITY = LIBRARY.timeml.MODALITY
POLARITY = LIBRARY.timeml.POLARITY


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
        self.attrs = { #EID: None, EIID: None,
                       ORIGIN: EVITA,
                       CLASS: feats.evClass,
                       TENSE: feats.tense,
                       ASPECT: feats.aspect,
                       POS: feats.nf_morph }
        if feats.modality != 'NONE':
            self.attrs[MODALITY] = feats.modality
        if feats.polarity != 'POS':
            self.attrs[POLARITY] = "NEG"

    def __str__(self):
        feats = ' '.join(["%s=%s" % (f, v) for (f, v) in self.attrs.items()])
        return "<Event %s>" % feats
