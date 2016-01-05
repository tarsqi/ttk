"""

Some utilities common to all the objects in the common_modules module.

"""

# The following functions all collect information from a tree topped by a
# node. The general mode is to descend the tree left-to-right and depth-first,
# test whether the node should be collected, and add the node to the result if
# the test is positive. They require the node to have a dtrs attribute and that
# the test is defined on them.

def get_words(node):
    """Return the list of words in node."""
    return [t.text for t in get_tokens(node)]

def get_words_as_string(node):
    """Return the list of words in node as a space-separated string."""
    return ' '.join(get_words(node))

def get_tokens(node, result=None):
    """Return the list of Tokens in node."""
    if result is None:
        result = []
    for dtr in node.dtrs:
        if dtr.isToken():
            result.append(dtr)
        get_tokens(dtr, result)
    return result

def get_events(node, result=None):
    """Return the list of Tokens in node."""
    if result is None:
        result = []
    for dtr in node.dtrs:
        if dtr.isEvent():
            result.append(dtr)
        get_events(dtr, result)
    return result

