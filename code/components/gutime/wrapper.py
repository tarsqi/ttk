"""

Contains the GUTime wrapper.

The wrapper contains an optional call to BTime, governed by the variable USE_BTIME. This
variable is set to False by default. Set it to True if you want to apply BTime, see
btime.py for reasons why using BTime does not make sense right now.

"""

# boolean to switch BTime on and off
USE_BTIME = False


import os
from time import time

from ttk_path import TTK_ROOT
from library.tarsqi_constants import GUTIME
from utilities.xml_utils import merge_tags_from_files, merge_tags_from_xmldocs
from utilities import logger
from docmodel.xml_parser import Parser, XmlDocument, XmlDocElement
from components.gutime.btime import BTime


class GUTimeWrapper:

    """Wrapper for GUTime."""
    

    def __init__(self, document):

        self.document = document
        self.component_name = GUTIME
        self.DIR_GUTIME = os.path.join(TTK_ROOT, 'components', 'gutime')
        self.DIR_DATA = os.path.join(TTK_ROOT, 'data', 'tmp')
        
        
    def process(self):

        """Get the XmlDOcument and call the Perl scripts that implement TempEx and GUTime. The
        GUTime scripts are gradually being replaced with Python code."""
        
        os.chdir(self.DIR_GUTIME)
        begin_time = time()

        xmldocs = [self.document.xmldoc]
        count = 0

        for xmldoc in xmldocs:

            count += 1
            fin = os.path.join(self.DIR_DATA, "frag%03d.gut.t1.xml" % count)
            fout = os.path.join(self.DIR_DATA, "frag%03d.gut.t2.xml" % count)
            
            self._prepare_gutime_input(xmldoc, fin)

            command = "perl TimeTag.pl %s > %s" % (fin, fout) 
            (fh_in, fh_out, fh_errors) = os.popen3(command)
            for line in fh_errors:
                logger.warn(line)

            # get the gutime result, remove the DATE_LINE tag and its
            # content, merge the results into xmldoc and apply btime
            xmldoc_out = Parser().parse_file(open(fout,"r"))
            self._remove_datetime(xmldoc_out)
            merge_tags_from_xmldocs(xmldoc, xmldoc_out)
            if USE_BTIME:
                BTime().process_xmldoc(xmldoc)

        logger.info("%s DONE, processing time was %.3f seconds" %
                    (self.component_name, time() - begin_time))
        os.chdir(TTK_ROOT)


    def _prepare_gutime_input(self, xmldoc, filename):

        """Takes an xmldoc (a slice of the entire document) and creates the input file for
        GUTime."""

        # assume that the first element is an opening tag
        opentag = xmldoc.elements[0]
        new_elements = opentag.get_slice()

        # crate new xmldoc to copy contents into, this is needed
        # because we will remove most tags
        new_xmldoc = XmlDocument()
        new_xmldoc.populate_doc_from_list(new_elements)

        # remove all tags from the body except <s>, <lex> and the content tag
        #content_tag = self.tarsqi_instance.content_tag
        content_tag = 'TEXT'
        for el in new_xmldoc.elements:
            if el.is_opening_tag():
                if not el.tag in ['s', 'lex', content_tag]:
                    el.remove()
                
        change_root_tag(new_xmldoc, content_tag, 'DOC')
    
        # add a DATE_TIME tag with the DCT
        el1 = XmlDocElement('<DATE_TIME>', tag='DATE_TIME', attrs={})
        el2 = XmlDocElement(self.document.get_dct())
        el3 = XmlDocElement('</DATE_TIME>', tag='DATE_TIME')
        new_xmldoc.elements[0].insert_element_after(el3)
        new_xmldoc.elements[0].insert_element_after(el2)
        new_xmldoc.elements[0].insert_element_after(el1)

        # save the GUTime input
        new_xmldoc.save_to_file(filename)


    def _remove_datetime(self, xmldoc):

        """Removes the DATE_TIME tag and its contents from xmldoc. Removes the slice from the
        linked list and the embedded TIMEX3 from the timex tags list."""
        
        open_datetime = xmldoc.get_tags('DATE_TIME')[0]
        datetime_slice = open_datetime.get_slice()
        for el in datetime_slice:
            el.remove()
        try:
            xmldoc.tags['TIMEX3'].remove(open_datetime.next)
        except ValueError:
            logger.warn("Could not remove TIMEX3 in DATE_TIME tag - ValueError")
        except AttributeError:
            logger.warn("Could not remove TIMEX3 in DATE_TIME tag - AttributeError")

            
def change_root_tag(xmldoc, oldname, newname):

    """Replace the name of the root tag with tagname."""

    opening_tag = xmldoc.elements[0]
    closing_tag = xmldoc.elements[-1]
    opening_tag.tag = newname
    closing_tag.tag = newname
    opening_tag.content = opening_tag.content.replace('<'+oldname,'<'+newname)
    closing_tag.content = closing_tag.content.replace('</'+oldname,'</'+newname)
    
