RELMAPPING1a = {
    # maps TimeML relations to Allen relations
    'BEFORE': '<', 'IBEFORE': 'm', 'AFTER': '>', 'IAFTER': 'mi',
    'INCLUDES': 'di', 'IS_INCLUDED': 'd',
    'DURING_INV': 'di',
    'BEGINS': 's', 'BEGUN_BY': 'si', 'ENDS': 'f', 'ENDED_BY': 'fi',
    'IDENTITY': '=', 'SIMULTANEOUS': '=', 'DURING': '='
}


def translate_timeml_relation(reltype):
    """Look up a TimeML relation in the table and return it as an interval
    relation."""
    # TODO: need to revisit this mapping
    return RELMAPPING1a.get(reltype)


RELMAPPING1b = {
    # maps TimeML relations to Allen relations
    '<': 'BEFORE', 'm': 'IBEFORE', '>': 'AFTER', 'mi': 'IAFTER',
    'di': 'INCLUDES', 'd': 'IS_INCLUDED',
    's': 'BEGINS', 'si': 'BEGUN_BY', 'f': 'ENDS', 'fi': 'ENDED_BY',
    '=': 'IDENTITY|SIMULTANEOUS|DURING'
}


def translate_interval_relation(reltype):
    """Look up a TimeML relation in the table and return it as an interval
    relation."""
    # TODO: need to revisit this mapping
    return RELMAPPING1b.get(reltype)


RELMAPPING2 = {
    # maps TimeML relations to their inverses
    'BEFORE': 'AFTER', 'IBEFORE': 'IAFTER',
    'AFTER': 'BEFORE', 'IAFTER': 'IBEFORE',
    'INCLUDES': 'IS_INCLUDED', 'IS_INCLUDED': 'INCLUDES',
    'BEGINS': 'BEGUN_BY', 'BEGUN_BY': 'BEGINS',
    'ENDS': 'ENDED_BY', 'ENDED_BY': 'ENDS',
    'IDENTITY': 'IDENTITY', 'SIMULTANEOUS': 'SIMULTANEOUS',
    'DURING': 'SIMULATANEOUS'
}


def invert_timeml_relation(reltype):
    """Look up the TimeML relation in the table and return its inverse."""
    # TODO: need to revisit this mapping (on DURING)
    return RELMAPPING2.get(reltype)


RELMAPPING3 = {
    # maps Allen relations to their inverses
    '<': '>',  '>': '<', 'm': 'mi', 'mi': 'm',
    'd': 'di', 'di': 'd',
    's': 'si', 'si': 's', 'f': 'fi', 'fi': 'f',
    'o': 'oi', 'oi': 'o',
    '=': '=',
}


def invert_interval_relation(relations):
    """Take a disjunction of interval relations represented as a string,
    replace each disjunct with its inverse and return the result."""
    result = []
    for rel in relations.split():
        result.append(RELMAPPING3[rel])
    result.sort()
    return ' '.join(result)


RELMAPPING4 = {
    # Maps the full name of a convex relation to its abbreviation
    '<': '<',
    '< = d di f fi m o oi s si': 'bd',
    '< d m o s': 'sb',
    '< di fi m o': 'ol',
    '< m o': 'ob',
    '=': '=',
    '= > d di f fi mi o oi s si': 'db',
    '= d di f fi o oi s si': 'ct',
    '= f fi': 'tt',
    '= s si': 'hh',
    '>': '>',
    '> d f mi oi': 'yo',
    '> di mi oi si': 'sv',
    '> mi oi': 'ys',
    'd': 'd',
    'd f oi': 'yc',
    'd o s': 'bc',
    'di': 'di',
    'di fi o': 'oc',
    'di oi si': 'sc',
    'f': 'f',
    'fi': 'fi',
    'm': 'm',
    'mi': 'mi',
    'o': 'o',
    'oi': 'oi',
    's': 's',
    'si': 'si'
}


def abbreviate_convex_relation(rel):
    return RELMAPPING4.get(rel, rel)
