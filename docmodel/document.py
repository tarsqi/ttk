
"""TarsqiDocument and friends.

This module contains TarsqiDocument and some of the classes used by it.

"""

import sys, codecs, StringIO, itertools
from xml.sax.saxutils import escape, quoteattr

from library.main import LIBRARY
from utilities import logger


TIMEX = LIBRARY.timeml.TIMEX
EVENT = LIBRARY.timeml.EVENT
ALINK = LIBRARY.timeml.ALINK
SLINK = LIBRARY.timeml.SLINK
TLINK = LIBRARY.timeml.TLINK

TID = LIBRARY.timeml.TID
EID = LIBRARY.timeml.EID
EIID = LIBRARY.timeml.EIID

TIME_ID = LIBRARY.timeml.TIME_ID
EVENT_INSTANCE_ID = LIBRARY.timeml.EVENT_INSTANCE_ID
RELATED_TO_TIME = LIBRARY.timeml.RELATED_TO_TIME
SUBORDINATED_EVENT_INSTANCE = LIBRARY.timeml.SUBORDINATED_EVENT_INSTANCE
RELATED_TO_EVENT_INSTANCE = LIBRARY.timeml.RELATED_TO_EVENT_INSTANCE


class TarsqiDocument:

    """An instance of TarsqiDocument should contain all information that may be
    needed by the wrappers to do their work. It includes the source, metadata,
    processing options, a set of identifier counters and a TagRepository.

    Instance Variables:
       source    -  an instance of DocSource
       metadata  -  a dictionary
       options   -  the Options instance from the Tarsqi instance
       tags      -  an instance of TagRepository
       counters  -  a set of counters used to create unique identifiers

    Note that he processing options are available to the wrappers only through
    this class by accessing the options variable."""

    def __init__(self):
        self.sourcedoc = None
        self.metadata = {}
        self.options = {}
        self.tags = TagRepository()
        self.counters = {TIMEX: 0, EVENT: 0, ALINK: 0, SLINK: 0, TLINK: 0}

    def __str__(self):
        fname = self.sourcedoc.filename if self.sourcedoc is not None else None
        return "<TarsqiDocument on %s>" % fname

    def add_options(self, options):
        self.options = options

    def get_dct(self):
        return self.metadata.get('dct')

    def text(self, p1, p2):
        return self.sourcedoc.text[p1:p2]

    def elements(self):
        """Method that returns the tags that contain paragraphs, that is, the
        tags of type docelement."""
        return self.tags.find_tags('docelement')

    def events(self):
        """Convenience method for easy access to events."""
        return self.tags.find_tags(EVENT)

    def timexes(self):
        """Convenience method for easy access to timexes."""
        return self.tags.find_tags(TIMEX)

    def slinks(self):
        return self.tags.find_tags(SLINK)

    def tlinks(self):
        return self.tags.find_tags(TLINK)

    def has_event(self, begin, end):
        """Return True if there is already an event at the given begin and
        end."""
        for tag in self.tags.find_tags(EVENT):
            if tag.begin == begin and tag.end == end:
                return True
        return False

    def add_timex(self, begin, end, attrs):
        """Add a TIMEX3 tag to the tag repository."""
        self.tags.add_tag('TIMEX3', begin, end, attrs)

    def add_event(self, begin, end, attrs):
        """Add an EVENT tag to the tarsqi_tags tag repository."""
        self.tags.add_tag('EVENT', begin, end, attrs)

    def pp(self, source_tags=True, tarsqi_tags=True):
        print "\n", self, "\n"
        for key, value in self.metadata.items():
            print "   metadata.%-14s  -->  %s" % (key, value)
        for key, value in self.options.items():
            print "   options.%-15s  -->  %s" % (key, value)
        if source_tags:
            print "\nSOURCE_TAGS:"
            self.sourcedoc.tags.pp()
        if tarsqi_tags:
            print "\nTARSQI_TAGS:"
            self.tags.pp()
        print

    def next_event_id(self):
        self.counters[EVENT] += 1
        return "e%d" % self.counters[EVENT]

    def next_timex_id(self):
        self.counters[TIMEX] += 1
        return "t%d" % self.counters[TIMEX]

    def next_link_id(self, link_type):
        """Return a unique lid. The link_type argument is one of {ALINK, SLINK,
         TLINK} and determines what link counter is incremented. The lid itself
         is the sum of all the link counts. Assumes that all links are added
         using the link counters in the document. Breaks down if there are
         already links added without using those counters."""
        self.counters[link_type] += 1
        return "l%d" % sum([self.counters[lt] for lt in (ALINK, SLINK, TLINK)])

    def remove_tlinks(self):
        """Remove all TLINK tags from the tags repository."""
        self.tags.remove_tags(TLINK)

    def print_source(self, fname):
        """Print the original source of the document, without the tags to file
        fname."""
        self.sourcedoc.print_source(fname)

    def print_sentences(self, fname=None):
        """Write to file (or stadard output if no filename was given) a Python
        variable assignment where the content of the variable the list of
        sentences as a list of lists of token strings."""
        fh = sys.stdout if fname is None else codecs.open(fname, mode='w',
                                                          encoding='UTF-8')
        fh.write("sentences = ")
        fh.write(str(self.list_of_sentences()))
        fh.write("\n")

    def print_all(self, fname=None):
        """Write source string, metadata, comments, source tags and tarsqi tags
        all to one file or to the standard output."""
        if fname is None:
            fh = sys.stdout
        else:
            fh = codecs.open(fname, mode='w', encoding='UTF-8')
        fh.write("<ttk>\n")
        fh.write("<text>%s</text>\n" % escape(self.sourcedoc.text))
        self._print_comments(fh)
        self._print_metadata(fh)
        self._print_tags(fh, 'source_tags', self.sourcedoc.tags.tags)
        self._print_tags(fh, 'tarsqi_tags', self.tags.tags)
        fh.write("</ttk>\n")

    def _print_comments(self, fh):
        if self.sourcedoc.comments:
            fh.write("<comments>\n")
            for offset in sorted(self.sourcedoc.comments.keys()):
                for comment in self.sourcedoc.comments[offset]:
                    comment = escape(comment.replace("\n", '\\n'))
                    fh.write("  <comment offset=\"%s\">%s</comment>\n"
                             % (offset, comment))
            fh.write("</comments>\n")

    def _print_metadata(self, fh):
        fh.write("<metadata>\n")
        for k, v in self.metadata.items():
            fh.write("  <%s value=\"%s\"/>\n" % (k, v))
        fh.write("</metadata>\n")

    def _print_tags(self, fh, tag_group, tags):
        fh.write("<%s>\n" % tag_group)
        for tag in sorted(tags):
            try:
                ttk_tag = tag.as_ttk_tag()
                # This became needed after allowing any text in the value of the
                # form and lemma attribute.
                if isinstance(ttk_tag, str):
                    ttk_tag = unicode(ttk_tag, errors='ignore')
                fh.write("  %s\n" % ttk_tag)
            except UnicodeDecodeError:
                # Not sure why this happened, but there were cases where the
                # result of as_ttk_tag() was a byte string with a non-ascii
                # character. The code in the try clause was changed to prevent
                # the error, but leave the except here just in case.
                logger.error("UnicodeDecodeError on printing a tag.")
        fh.write("</%s>\n" % tag_group)

    def list_of_sentences(self):
        sentences = []
        sentence = []
        for element in self.elements:
            for t in element.tarsqi_tags.tags:
                if t.name == 's':
                    if sentence:
                        sentences.append(sentence)
                        sentence = []
                elif t.name == 'lex':
                    sentence.append(self.text(t.begin, t.end))
            if sentence:
                sentences.append(sentence)
            sentence = []
        return sentences


class SourceDoc:

    """A SourceDoc is created by a SourceParser and contains source data and
    annotations of those data. The source data are put in the text variable as a
    unicode string, tags are in the source_tags and tarsqi_tags variables and
    contain begin and end positions in the source. In addition, metadata,
    comments, and any other data from the input is stored here.

    Note that the SourceDoc is the input to further Tarsqi processing and it
    stores everything that was given as input to the pipeline. This could be a
    text document or a TimeBank document without any TimeML annotations. But it
    could also be a TTK document that was the result of prior application of
    another pipeline and that document can contain Tarsqi tags. The metadata and
    tarsqi_tags will be exported to the relevant places in the TarsqiDocument
    when the metadata parse and the document structure parsers apply to the
    TarsqiDocument."""

    def __init__(self, filename='<STRING>'):
        """Initialize a SourceDoc on a filename or a string."""
        self.filename = filename
        self.xmldecl = None
        # initialize as a string buffer, will be a string later
        self.text = StringIO.StringIO()
        self.processing_instructions = {}
        self.comments = {}
        self.metadata = {}
        self.tags = TagRepository()
        self.offset = 0

    def __getitem__(self, i):
        return self.text[i]

    def add_opening_tag(self, name, attrs):
        """Add an opening tag to source_tags. This is used by the
        StartElementHandler of the Expat parser in SourceParserXML."""
        opening_tag = OpeningTag(name, self.offset, attrs)
        self.tags.add_tmp_tag(opening_tag)

    def add_closing_tag(self, name):
        """Add a closing tag to source_tags. This is used by the
        EndElementHandler of the Expat parser in SourceParserXML."""
        closing_tag = ClosingTag(name, self.offset)
        self.tags.add_tmp_tag(closing_tag)

    def add_characters(self, string):
        """Add a character string to the source and increment the current
        offset. Used by the CharacterDataHandler of the Expat parser in
        SourceParserXML."""
        self.text.write(string)     # this is already unicode
        self.offset += len(string)

    def add_comment(self, string):
        self.comments.setdefault(self.offset, []).append(string)

    def add_processing_instruction(self, target, data):
        td = (target, data)
        self.processing_instructions.setdefault(self.offset, []).append(td)

    def finish(self):
        """Transform the source text list into a string, merge the begin and end
        tags, and index the tags on offsets. This should be called by
        SourceParserXML which uses the Expat parser and looks for individual
        elements, it is not needed by SourceParserTTK since it uses a DOM
        object, it is also not needed by SourceParserText since it does not deal
        with tags."""
        string_buffer = self.text
        self.text = string_buffer.getvalue()
        string_buffer.close()
        self.tags.merge()
        self.tags.index()

    def pp(self):
        """Print source and tags."""
        print "\n<SourceDoc on '%s'>\n" % self.filename
        print self.text.encode('utf-8').strip()
        print "\nMETADATA:", self.metadata
        print "\nTAGS:"
        self.tags.pp()
        print
        # print "XMLDECL:", self.xmldecl
        # print "COMMENTS:", self.comments
        # print "PROCESSING:", self.processing_instructions

    def print_source(self, filename):
        """Print the source string to a file, using the utf-8 encoding."""
        fh = open(filename, 'w')
        fh.write(self.text.encode('utf-8'))


class TagRepository:

    """Class that provides access to the tags for a document. An instance of this
    class is used for the DocSource instance, other instances will be used for
    the elements in a TarsqiDocument. For now, the repository has the following
    structure:

    self.tmp
       A list of OpeningTag and ClosingTag elements, used only to build the tags
       list.

    self.tags
       A list with Tag instances.

    self.opening_tags
       A dictionary of tags indexed on begin offset, the values are lists of Tag
       instances, again ordered on id (thereby reflecting text order, but only
       for tags in the original input).

    self.closing_tags
       A dictionary indexed on end offset and begin offset, the values are
       dictionary of tagnames. For example,
          closing_tags[547][543] = {'lex':True, 'NG':True }
       indicates that there is both a lex tag and an NG tag from 543-547. The
       opening tags dictionary will have encoded that the opening NG occurs
       before the opening lex:
          opening_tags[543] = [<Tag 204 NG 543-547 {}>, <Tag 205 lex 543-547 {...}]

    """

    # TODO: the closing_tags dictionary is delusional in that it cannot deal
    # with multiple tags with the same name, begin and end. The question is
    # whether the opening and closing tags are needed, all they seem to do is be
    # there for when we create an XML document, which we may want to relegate to
    # another component alltogether.

    def __init__(self):
        self.tmp = []
        self.tags = []
        self.opening_tags = {}
        self.closing_tags = {}
        self.eid2event = {}
        self.tid2timex = {}

    def reset(self):
        self.__init__()

    def all_tags(self):
        return self.tags

    def add_tmp_tag(self, tagInstance):
        """Add an OpeningTag or ClosingTag to a temporary list. Used by the XML
        handlers."""
        self.tmp.append(tagInstance)

    def add_tag(self, name, begin, end, attrs):
        """Add a tag to the tags list and the opening_tags and closing_tags
        dictionaries."""
        tag = Tag(name, begin, end, attrs)
        self.tags.append(tag)
        self.opening_tags.setdefault(begin, []).append(tag)
        self.closing_tags.setdefault(end, {}).setdefault(begin, {})[tag.name] = True

    def append(self, tag):
        """Appends an instance of Tag to the tags list."""
        self.tags.append(tag)

    def remove_tags(self, tagname):
        """Remove all tags with name=tagname. Rebuilds the indexes after
        removing the tags."""
        self.tags = [t for t in self.tags if t.name != tagname]
        self.index()

    def remove_tag(self, tag):
        """Remove the tag from the list of tags. This is rather inefficient since the
        whole list is traversed. Also note that this method does not remove the
        tag from the opening_tags and closing_tags dictionaries, so depending on
        when this is done these may need to be re-indexed."""
        self.tags = [t for t in self.tags if t is not tag]

    def merge(self):
        """Take the OpeningTags and ClosingTags in self.tmp and merge them into
        Tags. Raise errors if tags do not match."""
        stack = []
        for t in self.tmp:
            if t.is_opening_tag():
                stack.append(t)
            elif t.name == stack[-1].name:
                t1 = stack.pop()
                tag = Tag(t1.name, t1.begin, t.end, t1.attrs)
                # We are not bothering to use add_tag since we will be building
                # the index right after the merge.
                self.tags.append(tag)
            else:
                raise TarsqiInputError("non-matching tag %s" % t)
        if stack:
            raise TarsqiInputError("no closing tag for %s" % stack[-1])
        self.tags.sort()

    def index(self):
        """Index tags on position."""
        self.opening_tags = {}
        self.closing_tags = {}
        for tag in self.tags:
            self.opening_tags.setdefault(tag.begin, []).append(tag)
            self.closing_tags.setdefault(tag.end,
                                         {}).setdefault(tag.begin,
                                                        {})[tag.name] = True
        for (k, v) in self.opening_tags.items():
            self.opening_tags[k].sort()

    def index_events(self):
        self.eid2event = {}
        for tag in self.tags:
            if tag.name == EVENT:
                self.eid2event[tag.attrs[EIID]] = tag

    def index_timexes(self):
        # TODO: merge with ei2events and create id2tag, assumes all tags have
        # ids and they are unique
        self.tid2timex = {}
        for tag in self.tags:
            if tag.name == TIMEX:
                self.tid2timex[tag.attrs[TID]] = tag

    def find_tags(self, name, begin=None, end=None):
        """Return all tags of this name. If the optional begin and end are given
        only return the tags that fall within those boundaries."""
        tags = sorted([t for t in self.tags if t.name == name])
        if begin is not None and end is not None:
            tags = [t for t in tags if begin <= t.begin and t.end <= end]
        return tags

    def find_linktags(self, name, o1, o2):
        """Return all the link tages with type name. Only include the ones that
        fall between offsets o1 and o2."""
        tags = []
        for tag in sorted([t for t in self.tags if t.name == name]):
            if name == SLINK:
                t1 = self.eid2event.get(tag.attrs.get(EVENT_INSTANCE_ID))
                t2 = self.eid2event.get(tag.attrs.get(SUBORDINATED_EVENT_INSTANCE))
            if name == ALINK:
                t1 = self.eid2event.get(tag.attrs.get(EVENT_INSTANCE_ID))
                t2 = self.eid2event.get(tag.attrs.get(RELATED_TO_EVENT_INSTANCE))
            if name == TLINK:
                t1 = self.eid2event.get(tag.attrs.get(EVENT_INSTANCE_ID))
                t2 = self.eid2event.get(tag.attrs.get(RELATED_TO_EVENT_INSTANCE))
                if t1 is None:
                    t1 = self.tid2timex.get(tag.attrs.get(TIME_ID))
                if t2 is None:
                    t2 = self.tid2timex.get(tag.attrs.get(RELATED_TO_TIME))
            offsets = [t1.begin, t1.end, t2.begin, t2.end]
            to1 = min(offsets)
            to2 = max(offsets)
            if o1 <= to1 and to2 <= o2:
                tags.append(tag)
        return tags

    def find_tag(self, name):
        """Return the first Tag object with name=name, return None if no such
        tag exists."""
        for t in self.tags:
            if t.name == name:
                return t
        return None

    def find_tags_at(self, begin_offset):
        """Return the list of tags which start at begin_offset."""
        return self.opening_tags.get(begin_offset, [])

    def import_tags(self, tag_repository, tagname):
        """Import all tags with name=tagname from tag_repository into self. This
        is mostly used when we want to take tags from the SourceDoc and add them
        to the tags on the TarsqiDocument."""
        for tag in tag_repository.find_tags(tagname):
            self.add_tag(tagname, tag.begin, tag.end, tag.attrs)

    def pp(self):
        self.pp_tags(indent='   ')
        # print; self.pp_opening_tags()
        # print; self.pp_closing_tags()

    def pp_tags(self, indent=''):
        for tag in self.tags:
            print "%s%s" % (indent, tag)

    def pp_opening_tags(self):
        print '<TagRepository>.opening_tags'
        for offset, list in sorted(self.opening_tags.items()):
            print("   %d "
                  % offset, "\n         ".join([x.__str__() for x in list]))

    def pp_closing_tags(self):
        print '<TagRepository>.closing_tags'
        for offset, dict in sorted(self.closing_tags.items()):
            print "   %d " % offset, dict


class Tag:

    """A Tag has a name, an id, a begin offset, an end offset and a dictionary of
    attributes. The id is handed in by the code that creates the Tag which could
    be: (1) the code that parses the source document, which will only assign an
    identifier if the source had an id attribute, (2) the preprocessor code,
    which assigns identifiers for lex, ng, vg and s tags, or (3) one of the
    components that creates tarsqi tags, in which case the identifier is None,
    but special identifiers like eid, eiid, tid and lid are used."""

    def __init__(self, name, o1, o2, attrs):
        """Initialize name, begin, end and attrs instance variables and make sure
        that what we have can be turned into valid XML by removing duplicate
        attribute names."""
        self.name = name
        self.begin = o1
        self.end = o2
        # Sometimes attrs is None
        self.attrs = attrs or {}
        # In case existing tags have a begin or end attribute, replace it with a
        # generated new attribute name (if we have 'end', then the new attribute
        # name will be 'end-N' where N is 1 or a higher number if needed).
        for attr in ('begin', 'end'):
            if attr in self.attrs:
                self.attrs[self.new_attr(attr, self.attrs)] = self.attrs.pop(attr)

    def __str__(self):
        attrs = ''.join([" %s='%s'" % (k, v) for k, v in self.attrs.items()])
        return "<Tag %s %s:%s {%s }>" % \
               (self.name, self.begin, self.end, attrs)

    def __cmp__(self, other):
        """Order two Tags based on their begin offset and end offsets. Tags with
        an earlier begin will be ranked before tags with a later begin, with
        equal begins the tag with the higher end will be ranked first. Tags with
        no begin (that is, it is set to -1) will be ordered at the end. The
        order of two tags with the same begin and end is undefined."""
        if self.begin == -1:
            return 1
        if other.begin == -1:
            return -1
        begin_cmp = cmp(self.begin, other.begin)
        end_cmp = cmp(other.end, self.end)
        return end_cmp if begin_cmp == 0 else begin_cmp

    @staticmethod
    def new_attr(attr, attrs):
        counter = itertools.count(1, step=1)
        for c in counter:
            new_attr = "%s_%d" % (attr, c)
            if new_attr not in attrs:
                return new_attr

    def is_opening_tag(self):
        return False

    def is_closing_tag(self):
        return False

    def as_ttk_tag(self):
        """Return the tag as a tag in the Tarsqi output format."""
        begin = " begin=\"%s\"" % self.begin if self.begin >= 0 else ''
        end = " end=\"%s\"" % self.end if self.end >= 0 else ''
        return "<%s%s%s%s />" % (self.name, begin, end, self.attributes_as_string())

    def as_lex_xml_string(self, text):
        """Return an opening and closing tag wrapped around text. This is used only by
        the GUTime wrapper to create input for GUTime, and it therefore has a narrow
        focus and does not get all information from the tag."""
        return "<lex id=\"%s\" begin=\"%d\" end=\"%d\" pos=\"%s\">%s</lex>" % \
            (None, self.begin, self.end, str(self.attrs['pos']), escape(text))

    def attributes_as_string(self):
        """Return a string representation of the attributes dictionary."""
        # In rare cases the attribute can be None, which breaks quoteattr, so
        # coerce the attribute into a string
        def protect(text): return 'None' if text is None else text
        attrs = ["%s=%s" % (k, quoteattr(protect(v)))
                 for (k, v) in self.attrs.items()]
        return '' if not attrs else ' ' + ' '.join(sorted(attrs))


class OpeningTag(Tag):

    "Like Tag, but self.end is always None."""

    def __init__(self, name, offset, attrs):
        Tag.__init__(self, name, offset, None, attrs)

    def __str__(self):
        return "<OpeningTag %s %d %s>" % \
            (self.name, self.begin, str(self.attrs))

    def is_opening_tag(self):
        return True


class ClosingTag(Tag):

    "Like Tag, but self.begin and self.attrs are always None."""

    def __init__(self, name, offset):
        Tag.__init__(self, name, None, offset, None)

    def __str__(self):
        return "<ClosingTag %s %d>" % \
            (self.name, self.end)

    def is_closing_tag(self):
        return True


class TarsqiInputError(Exception):
    pass
