"""

Some utilities common to all the objects in the common_modules module.

"""

import types

from library import forms


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
    """Given a sequence of elements, collect all the token leaves and return
    them as a list."""
    # TODO: this can probably use get_tokens
    tokens = []
    for item in sequence:
        if item.isToken():
            tokens.append(item)
        elif item.isChunk():
            tokens += get_tokens(item)
        elif item.isEvent():
            tokens.append(item)
        elif item.isIimex():
            tokens += get_tokens(item)
        else:
            raise "ERROR: unknown item type: " + item.__class__.__name__
    return tokens


# Testing a sequence of Tokens

def contains_adverbs_only(sequence):
    """Return true if sequence only contains adverbs, return false otherwise. Return
    True if the argument is an empty sequence."""
    non_advs = [item for item in sequence if item.pos not in forms.partInVChunks2]
    return False if non_advs else True



# Removing interjections from a GramVChunkList

def remove_interjections(gchunklist):
    """Remove interjections and punctuations from gchunk, which is a
    GramVChunkList, where self.node is either a VerbChunk or a list of
    tokens. Examples:
       - ['ah', ',', 'coming', 'up']
         >> ['ah', 'coming', 'up']
       - ['she', 'has', ',',  'I', 'think', ',', 'to', 'go']
         >> ['she', 'has', 'to', 'go']"""
    # TODO. In the 6000 tokens of evita-test2.xml, this applies only once,
    # replacing 'has, I think, been' with 'has been', but that seems like an
    # error because the input had an extra verb after 'been' ('has, I think,
    # been demolished'). Could perhaps remove this method. Also, it is a bit
    # peculiar how 'has, I think, been' ends up as a sequence, find out why.
    before = []  # nodes before first punctuation
    after = []   # nodes after last punctuation
    for item in gchunklist.nodes:
        if item.pos not in (',', '"', '``'):
            before.append(item)
        else: break
    for item in reversed(gchunklist.nodes):
        if item.pos not in (',', '"', '``'):
            after.insert(0, item)
        else: break
    if len(before) == len(after) == len(gchunklist.nodes):
        # no punctuations or interjections
        return before
    elif len(before) + len(after) == len(gchunklist.nodes) - 1:
        # one punctuation
        return before + after
    else:
        # two punctuations with potential interjection
        return before + after
