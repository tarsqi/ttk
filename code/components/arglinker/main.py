"""

Main module for the ArgLinker component. 

ArgLinker is a simple Python placeholder for the later to be added
MaxEnt argument linker.

"""


from components.common_modules.component import TarsqiComponent
from library.tarsqi_constants import ARGLINKER
from docmodel.xml_parser import Parser
from utilities import logger
from utilities.converter import FragmentConverter      

#import utilities.logger as logger
#logger.initialize_logger("arglog", 4)



class ArgLinker (TarsqiComponent):

    """Simple Python place holder for a more sophisticated argument linker
    using a MaxEnt classifier.

    Instance variables:
       NAME - a string
       doctree - a Document"""
    
    def __init__(self):
        """Load the Slinket dictionaries if they have not been loaded yet."""
        self.NAME = ARGLINKER
        self.doctree = None

    def _extractLinks(self):
        # ** Document
        alllinks = []
        for linkset in self.xmldep.tags['dep_parse']:
            sentlinks = []
            for link in linkset.collect_contained_tags():
                if link.attrs.keys() == []: continue
                linktype = link.attrs['type']
                for component in link.collect_contained_tags():
                    if component.content == u'<gov>':
                        gov = component.collect_content()
                    if component.content == u'<dep>':
                        dep = component.collect_content()
                sentlinks.append((linktype, gov, dep))
            alllinks.append(sentlinks)
        return alllinks

    def _crawl(self, sent, objs=None):
    	if objs is None: objs = set()
	for obj in sent:
		if obj not in objs:
			objs.add(obj)
			self._crawl(obj, objs)
	return objs

    def _find_by_lid(self, sent, lid):
    	toks = [tok for tok in self._crawl(sent) if hasattr(tok, 'lid')]
	toks = [tok for tok in toks if tok.lid == lid]
	return toks[0]

    def process(self, infile, outfile, depfile):
        """Run the ArgLinker on the input file and write the results to the
        output file. Both input an doutput file are fragments. Uses
        the xml parser as well as the fragment converter to prepare
        the input and create the shallow tree that ArgLinker requires.
        Arguments:
           infile - an absolute path
           outfile - an absolute path"""


        # ** Run Ben's Dependency Parser on in file.
        #        depfile = infile + ".DEP"
        #        depfile = '/home/havasi/tarsqi/inputs/tb-ex1.xml.DEP'



        # ** Import the arglinks from Ben's Parsers
        arglinks = []
        
        #print 'processing doc'#__REMOVE
        try:
#            import ldebug
#            ldebug.object = self
            self.xmldoc = Parser().parse_file(open(infile,'r'))
            self.doctree = FragmentConverter(self.xmldoc, infile).convert(user=ARGLINKER)
            self.xmldep = Parser().parse_file(open(depfile,'r'))
            arglinks = self._extractLinks()
            count = 0
            for sentence in self.doctree:
                alinks = []
                newlinks = self.getLinks(sentence, arglinks[count])
                alinks += newlinks
                self._create_arglinks(sentence, alinks)
                count += 1
        except Exception, e:
            import traceback
            traceback.print_exc()

        #self.doctree.printOut(outfile)
        self.xmldoc.save_to_file(outfile)

    def getLinks(self, sentence, args):
        nouns = []
        events = []
        for word in sentence:
            if  word.isNounChunk():
#                print "Noun hit", word.getHead()[0].lid
                nouns.append(word.getHead()[0].lid)
            if word.isChunk() and word.embedded_event():
#                print "Event Hit"
#                print word.embedded_event().get_event()[0].lid
                events.append(word.embedded_event().get_event()[0].lid)
#        print nouns
#        print events
        links = {}
        for link in args:
            linktype = link[0]
            eventID = link[1]
            nounID = link[2]
#            print eventID, nounID
            if eventID not in events: continue
            if nounID not in nouns: continue
            #print "hit"
            if links.has_key(eventID): links[eventID].append((nounID, linktype))
            else: links[eventID] = [(nounID, linktype)]

        args = []
        for event in links.keys():
            nounlist = links[event]
            if len(nounlist) == 1:
                if self._check_pair(nounlist[0][0], event, sentence): args.append((nounlist[0][1],nounlist[0][0], event))
            else:
                for noun in nounlist:
                    if self._check_pair(noun[0], event, sentence): args.append((noun[1], noun[0], event))
                    # If I have to pick just one
                    # Find the left and rightmost chunk
                    # Give pref to the one on the right, find the closest.
        return args


                    
    def _check_pair(self, noun, verb, sentence):
        # Make a list of relation types not to cross, for now just include punctuation
	#print 'in _check_pair...'
	#print noun, verb, sentence
	#sentence.pretty_print()
	#n = self._find_by_lid(sentence, noun)
	#v = self._find_by_lid(sentence, verb)
	#print 'Noun: '
	#n.pretty_print()
	#print 'Verb: '
	#v.pretty_print()
        return True

    def _create_arglinks(self, sentence, alinks):
        """For each noun group in the sentence, get the head and find a event
        that it is an argument of."""
        #print alinks
        if alinks == []: return
        for type, noun, event in alinks:
            #print noun
            # Marc: Given an ID such as "L4" how do I find the cooresponding chunk? 
            nchunk = self._find_by_lid(sentence, noun)
            event = self._find_by_lid(sentence, event)
            self._create_arglink(event, nchunk)
                
    def _create_arglink(self, event_token, argument):

        event = event_token.parent

        # check whether the argument is not an empty NG
        if len(argument) > 0:
            arg_head = argument
	    import ldebug
	    ldebug.object = event
	    #assert False
            if arg_head.isToken():
                pred = 'eventID="' + event.eid + '"'
                arg = 'argID="' + arg_head.lid + '"'
                text1 = 'text1="' + event_token.getText() + '"'
                text2 = 'text2="' + arg_head.getText() + '"'
                print "<ARGLINK %s %s argTag=\"lex\" role=\"UNKNOWN\" %s %s />" % \
                    (pred, arg, text1, text2)
                self.xmldoc.add_arglink(event.eid,
                                        arg_head.lid)
