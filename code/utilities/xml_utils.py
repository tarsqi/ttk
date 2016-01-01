
def endElementString(tagname):
    """Return the string representation of a closing tag given the tagname."""
    return '</'+tagname+'>'

def startElementString(tagname, attrs):
    """Return the string representation of an opening tag given the tagname and a dictionary
    of attributes."""
    string = '<'+tagname
    for att in attrs.items():
        name = att[0]
        value = att[1]
        if not (name is None or value is None):
            string = string+' '+name+'="'+value+'"'
    string = string+'>'
    return string

def emptyContentString(tagname, attrs):
    """Return the string representation of a non-consuming tag given the tagname and a
    dictionary of attributes."""
    opening_string = startElementString(tagname, attrs)
    return opening_string[:-1] + '/>'
