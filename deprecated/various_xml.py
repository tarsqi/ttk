class SourceDoc:

    """Some code removed from SourceDoc."""

     def print_tags(self, filename):
        """Print all the tags to a file. Each tag is printed on a tab-separated
        line with opening offset, closing offset, tag name, and attribute value
        pairs."""
        fh = open(filename, 'w')
        for t in self.source_tags.tags:
            fh.write("%d\t%d\t%s" % (t.begin, t.end, t.name))
            for (attr, val) in t.attrs.items():
                fh.write("\t%s=\"%s\"" % (attr, val.replace('"','&quot;')))
            fh.write("\n")


    def print_xml(self, filename):

        """Print self as an inline XML file. This should work on all input that
        did not generate a warning while parsing. The output file is identical
        to the input file modulo processing instructions, comments, and the
        order of attributes in an opening tag and the kind of quotes used. Also,
        tags that were printed as <SOME_TAG/> will be printed as two tags. There
        are no provisions for crossing tags. Therefore, the code is also not set
        up to deal with tags added to the tags repository since those may have
        introduced crossing tags."""

        # TODO: check what happens when input is not an xml file
        # TODO: add xmldec, processing instructions and comments

        xml_string = u''  # TODO: use a string buffer
        offset = 0
        stack = []

        for char in self.text:

            # any tags on the stack that can be closed?
            (stack, matching) = self._matching_closing_tags(offset, stack, [])
            for t in matching:
                xml_string += "</%s>" % t.name

            # any new opening tags?
            for t in self.source_tags.opening_tags.get(offset,[]):
                stack.append(t)
                xml_string += "<%s%s>" % (t.name, t.attributes_as_string())

            # any of those need to be closed immediately (non-consuming tags)?
            (stack, matching) = self._matching_closing_tags(offset, stack, [])
            for t in matching:
                xml_string += "</%s>" % t.name

            xml_string += escape(char)
            offset += 1

        fh = open(filename, 'w')
        fh.write(xml_string.encode('utf-8'))


    def _matching_closing_tags(self, offset, stack, matching):
        """Recursively return the closing tags that match the tail of the stack
        of opening tags."""
        if not stack:
            return (stack, matching)
        last = stack[-1]
        if self.source_tags.closing_tags.get(offset,{}).get(last.begin,{}).get(last.name,False):
            stack.pop()
            matching.append(last)
            return self._matching_closing_tags(offset, stack, matching)
        else:
            return (stack, matching)


