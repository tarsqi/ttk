
from docmodel.xml_parser import Parser, XmlDocElement, create_dct_element

from graph import Graph
from objects import Node, Edge, Constraint
from mappings import invert_timeml_relation
from mappings import translate_timeml_relation
from mappings import translate_interval_relation
from utils import CompositionTable
#from timeml_specs import TLINK, EVENT, INSTANCE, TIMEX, TID, EIID
#from timeml_specs import RELTYPE, EVENT_INSTANCE_ID, TIME_ID, CONFIDENCE
#from timeml_specs import RELATED_TO_EVENT_INSTANCE, RELATED_TO_TIME, ORIGIN
from library.timeMLspec import TLINK, EVENT, INSTANCE, TIMEX, TID, EIID
from library.timeMLspec import RELTYPE, EVENT_INSTANCE_ID, TIME_ID, CONFIDENCE
from library.timeMLspec import RELATED_TO_EVENT_INSTANCE, RELATED_TO_TIME, ORIGIN

DEBUG = False


class ConstraintPropagator:

    """Main SputLink class.
    
    Instance variables:
       file - a file object
       xmldoc - the Xml document created from the file
       grap - a Graph
       pending - a list
       compositions - a CompositionTable
       intersections - not yet used
    """
    
    def __init__(self):
        self.file = None
        self.xmldoc = None
        self.graph = Graph()
        self.pending = []
        self.compositions = None
        self.intersections = None

    def setup(self, compositions_file, tml_file):
        """Read the compositions table and export the compositions to the
        graph. Read the TimeML file and send the events, instances and
        timexes to the graph, and use the tlinks to build the pending
        queue."""
        self.compositions = CompositionTable(compositions_file)
        self.graph.compositions = self.compositions
        (events, instances, timexes, tlinks) = self._read_file(tml_file)
        self._load_objects(events, instances, timexes, tlinks)

    def setup_for_chronicler(self, compositions_file, timexes, tlinks):
        """Read the compositions table and export the compositions to
        the graph. Read the timexes and the tlinks as given by the
        chronicler. Send the events, instances and timexes to the
        graph, and use the tlinks to build the pending queue."""
        self.compositions = CompositionTable(compositions_file)
        self.graph.compositions = self.compositions
        timex_elements = []
        for timex in timexes:
            timex_elements.append(
                XmlDocElement('dummy', 'TIMEX3',
                              {'TYPE': 'DATE', 'VAL': timex.val, 'tid': timex.id }))
        tlink_elements = []
        for tlink in tlinks:
            tlink_elements.append(
                XmlDocElement('dummy', 'TLINK',
                              {'timeID': tlink.timeID,
                               'relType': tlink.relType,
                               'relatedToTime': tlink.relatedToTime,
                               'lid': tlink.id }))
        self._load_objects([], [], timex_elements, tlink_elements)

    def _read_file(self, file):
        """Read the contents of a TimeML file using the XML parser of the
        Tarsqi Toolkit. Extract all events, instances, timexes and
        tlinks and return these."""
        self.file = file.name
        self.graph.file = file.name
        self.xmldoc = Parser().parse_file(file)
        events = self.xmldoc.get_tags(EVENT)
        instances = self.xmldoc.get_tags(INSTANCE)
        timexes = self.xmldoc.get_tags(TIMEX)
        timexes.append(create_dct_element('DUMMY_VAL'))
        for t in timexes: print t
        tlinks = self.xmldoc.get_tags(TLINK)
        tlinks = self._filter_tlinks(tlinks)
        return (events, instances, timexes, tlinks)
    
    def _filter_tlinks(self, tlinks):
        """Return only the S2T links, the Blinker links and the classifier
        links with confidence of 0.95 or higher. This is here to mimic
        functionality of the Perl version of SputLink."""
        result = []
        for tlink in tlinks:
            origin = tlink.attrs[ORIGIN]
            #print origin
            if origin.startswith('CLASSIFIER'):
                confidence = float(origin.lstrip('CLASSIFIER '))
                threshold = 0.95
                #print confidence, threshold
                if confidence >= threshold:
                    #print confidence
                    result.append(tlink)
            else:
                result.append(tlink)
        return result
    
    def _load_objects(self, events, instances, timexes, tlinks):
        """Add the events, instances and timexes to the graph and the tlinks
        to the pending queue."""
        self.graph.add_nodes(events, instances, timexes)
        self._build_pending_queue(tlinks)        


    def _build_pending_queue(self, tlinks):

        """Take a list of tlinks, encoded as XmlDocElements, and add them to the
        pending queue as instances of Constraint."""
        
        for tlink in tlinks:
            #print tlink.attrs
            if not tlink.attrs.has_key(RELTYPE):
                continue
            id1 = tlink.attrs.get(EVENT_INSTANCE_ID, None)
            if not id1:
                id1 = tlink.attrs[TIME_ID]
            id2 = tlink.attrs.get(RELATED_TO_EVENT_INSTANCE, None)
            if not id2:
                id2 = tlink.attrs[RELATED_TO_TIME]
            # add the constraint
            rel = translate_timeml_relation(tlink.attrs[RELTYPE])
            constraint1 = Constraint(id1, rel, id2)
            constraint1.source = 'user'
            constraint1.history = tlink
            self.pending.append(constraint1)
            # ... and its inverse
            # (this is definitely needed, without it, even when all
            # user links are on one side of the graphs, we do not find
            # all new constraints, ***find out why***)
            rel = invert_timeml_relation(tlink.attrs[RELTYPE])
            rel = translate_timeml_relation(rel)
            constraint2 = Constraint(id2, rel, id1)
            constraint2.source = 'user-inverted'
            constraint2.history = constraint1
            self.pending.append(constraint2)
            
    
    def reset(self):
        """Reset the file, graph and pendng instance variables."""
        self.file = None
        self.graph = Graph()
        self.pending = []

    def add_constraint(self):
        """Pop a Constraint from the pending list if it is not empty and ask
        the graph to propagate it.."""
        if self.pending:
            constraint = self.pending.pop(0)
            self.graph.propagate(constraint)
            if DEBUG:
                graph_file = "data/graphs/graph.%02d.html" % self.graph.cycle
                self.pp_graph(graph_file)

    def add_constraints(self, force=False, threshold=0):
        """Add all constraints to the graph, which will propagate them in
        turn. Currently hands all constraints to the graph. A later
        version will either use a confidence threshold under which
        constraints will not be added or some other mechanism to
        create the pending queue. Also, the force parameter is not yet
        used."""
        while self.pending:
            self.add_constraint()

    def reduce_graph(self):
        """Ask the graph to reduce itself."""
        self.graph.reduce()
        
    def create_output(self, outfile):
        """Take the edges from the graph and add them to the xml document as
        tlinks."""
        self.xmldoc.remove_tags(TLINK)
        for edge in self.graph.get_edges():
            id1 = edge.node1
            id2 = edge.node2
            origin = edge.constraint.source
            tag_or_constraint = edge.constraint.history
            try:
                # constraint is from a tlink
                origin = tag_or_constraint.attrs[ORIGIN]
                reltype = tag_or_constraint.attrs[RELTYPE]
            except AttributeError:
                # constraint is from an inverted tlink
                origin = tag_or_constraint.history.attrs[ORIGIN] + ' i'
                reltype = tag_or_constraint.history.attrs[RELTYPE]
                reltype = invert_timeml_relation(reltype)
            self.xmldoc.add_tlink(reltype, id1, id2, origin)
        self.xmldoc.save_to_file(outfile)

    def pp_graph(self, file):
        """Print the graph in an HTML table."""
        self.graph.pp(file)

    def pp_compositions(self, filename):
        """Print the composition table to an HTML table."""
        self.compositions.pp(filename)
