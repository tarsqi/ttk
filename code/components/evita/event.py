from utilities.xml_utils import startElementString, endElementString, emptyContentString
from docmodel.xml_parser import XmlDocElement

class Event:

    def __init__(self, gramCh):
        tokenList = [gramCh.head]
        self.tokenList = tokenList
        self.attrs = {
            "eid": None,
            "class": None
            }
        self.instanceList = []
        self.addInstance()
        
        self.setAttribute("class", gramCh.evClass)
        self.setAttribute("tense", gramCh.tense)
        self.setAttribute("aspect", gramCh.aspect)
        self.setAttribute("pos", gramCh.nf_morph)
        if gramCh.modality != 'NONE':
            self.setAttribute("modality", gramCh.modality)
        if gramCh.polarity != 'POS':
            self.setAttribute("polarity", "NEG")
            
    def setAttribute(self, attr, value):
        if attr == "class":
            self.attrs["class"] = value
        else:
            for instance in self.instanceList:
                instance.setAttribute(attr, value)
            
    def addInstance(self, instance = None):
        if instance is None: instance = Instance(self)
        self.instanceList.append(instance) 
    
    # this method is here for backwards compatibility, use setAttribute() now
    def setClass(self, value):
        self.attrs["class"] = value

    def addToXmlDoc(self):
        """Add self to xmldocument by making xmldocelements for start and end and
        instances, retrieving begin and end token xmldocelements from tokenList and adding
        our start element before the first open tag, our end element after the last close,
        and our instances after that"""
        self.tokenList[0].lex_tag_list[0].insert_element_before(self.startElement())
        endTokenElem = self.tokenList[-1].lex_tag_list[-1]
        endTokenElem.insert_element_after(self.endElement())
        for i in range(len(self.instanceList)):
            endTokenElem = endTokenElem.get_next()
            endTokenElem.insert_element_after(self.instanceList[i].element())

    def startElementString(self):
        """return startElementString representing our start"""
        return startElementString("EVENT", self.attrs)

    def endElementString(self):
        """return endElementString representing our end"""
        return endElementString("EVENT")
        
    def startElement(self):
        """return xmldocelement representing our start"""
        startString = self.startElementString()
        return XmlDocElement(startString, "EVENT", self.attrs)
        
    def endElement(self):
        """return xmldocelement representing our end"""
        endString = self.endElementString()
        return XmlDocElement(endString, "EVENT")


class Instance:

    def __init__(self, event):
        self.event = event
        self.attrs = { "eiid": None, "eventID": None,
                       "cardinality": None, "modality": None, "polarity": "POS", 
                       "tense": "NONE", "aspect": "NONE", "pos": "NONE" }

    def setAttribute(self, attr, value):
        if self.attrs.has_key(attr):
            self.attrs[attr] = value
        else:
            raise Error("no such attribute: "+attr)

    def elementString(self):
        """return an elementString representing us"""
        return emptyContentString("MAKEINSTANCE", self.attrs)

    def element(self):
        """return an xmldocement representing us"""
        elementString = self.elementString()
        return XmlDocElement(elementString, "MAKEINSTANCE", self.attrs)
