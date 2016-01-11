"""

Some utilities common to all the objects in the common_modules module.

"""

import types


def get_tokens(node_or_sequence):
    """Get tokens from a node or sequence."""
    if type(node_or_sequence) in (types.TupleType, types.ListType):
        return get_tokens_from_sequence(node_or_sequence)
    else:
        return get_tokens_from_node(node_or_sequence)


# The following functions all collect information from a tree topped by a
# node. The general mode is to descend the tree left-to-right and depth-first,
# test whether the node should be collected, and add the node to the result if
# the test is positive. They require the node to have a dtrs attribute and that
# the test is defined on them.

def get_words(node):
    """Return the list of words in node."""
    return [t.text for t in get_tokens_from_node(node)]

def get_words_as_string(node):
    """Return the list of words in node as a space-separated string."""
    return ' '.join(get_words(node))

def get_tokens_from_node(node, result=None):
    """Return the list of Tokens in the tree starting at node."""
    if result is None:
        result = []
    for dtr in node.dtrs:
        if dtr.isToken():
            result.append(dtr)
        get_tokens_from_node(dtr, result)
    return result

def get_events(node, result=None):
    """Return the list of EventTags in the tree starting at node."""
    if result is None:
        result = []
    for dtr in node.dtrs:
        if dtr.isEvent():
            result.append(dtr)
        get_events(dtr, result)
    return result


# Collect information from a sequence of nodes

def get_tokens_from_sequence(sequence):
    """Given a sequence of elements which is a slice of a tree, collect all token
    leaves and return them as a list. This is different from what get_tokens in
    utils does since it operates on a list instead of a single node."""
    tokens = []
    for item in sequence:
        if item.nodeType[-5:] == 'Token':
            tokens.append(item)
        elif item.nodeType[-5:] == 'Chunk':
            tokens += get_tokens(item)
        elif item.nodeType == 'EVENT':
            tokens.append(item)
        elif item.nodeType == 'TIMEX3':
            tokens += get_tokens(item)
        else:
            raise "ERROR: unknown item type: " + item.nodeType
    return tokens

