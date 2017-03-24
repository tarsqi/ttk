

def intersect_relations(rels1, rels2):
    """Returns the intersection of two relation sets. Returns None if both
    of the two sets are None."""
    # TODO: the description does not fit the code
    if rels2 is None:
        return rels1
    if rels1 is None:
        return rels2
    rels1_dict = {}
    intersection = []
    for rel in rels1.split():
        rels1_dict[rel] = 1
    for rel in rels2.split():
        if rel in rels1_dict:
            intersection.append(rel)
    intersection.sort()
    return ' '.join(intersection)


def intersect_lists(l1, l2):
    """Returns the intersection of two lists. The result will not contain
    duplicate elements and list order is not preserved."""
    return list(set(l1).intersection(set(l2)))


def compare_id(a, b):
    if a.startswith('e') and b.startswith('t'):
        return -1
    if a.startswith('t') and b.startswith('e'):
        return 1
    a = int(a.lstrip('eit'))
    b = int(b.lstrip('eit'))
    if a < b:
        return -1
    else:
        return 1


class CompositionTable:

    """Implements the 28 by 28 composition table. Takes care of loading
    the table from file and retrieving compositions from the table."""

    def __init__(self, compositions_file):
        """Read the compositions file and load all compositions into the
        data instance variable."""
        all_rels = {}
        all_compositions = []
        for line in open(compositions_file):
            (rel1, rel2, rel3) = [r.strip() for r in line.split("\t")]
            all_rels[rel1] = True
            all_compositions.append((rel1, rel2, rel3))
        self.data = {}
        self.data2 = {}
        for rel1 in all_rels:
            self.data[rel1] = {}
            for rel2 in all_rels:
                self.data[rel1][rel2] = None
        for (r1, r2, r3) in all_compositions:
            self.data[r1][r2] = r3

    def compose_rels(self, rel1, rel2):
        """Looks up the composition of rel1 and rel2 and returns it."""
        return self.data[rel1][rel2]

    def pp(self, filename):
        """Print an html table to filename."""
        file = open(filename, 'w')
        file.write("<html>\n")
        file.write("<head>\n<style type=\"text/css\">\n<!--\n")
        file.write("body { font-size: 14pt }\n")
        file.write("table { font-size: 14pt }\n")
        file.write("-->\n</style>\n</head>\n")
        file.write("<body>\n\n")
        file.write("<table cellpadding=3 cellspacing=0 border=1>\n")
        file.write("\n<tr>\n\n")
        file.write("  <td>&nbsp;\n\n")
        rels = self.data.keys()
        rels.sort()
        for rel in rels:
            rel = massage(rel)
            file.write("  <td>%s\n" % rel)
        for r1 in rels:
            file.write("\n\n<tr>\n\n")
            header = massage(r1)
            file.write("  <td>%s\n" % header)
            for r2 in rels:
                r = self.data[r1][r2]
                if r is None:
                    r = ' '
                r = massage(r)
                file.write("  <td>%s\n" % r)
        file.write("</table>\n</body>\n</html>\n\n")


def massage(str):
    """Prepare the string representation of a relation set for printing in
    html."""
    str = str.replace('<', '&lt;')
    str = str.replace('>', '&gt;')
    str = str.replace(' ', '&nbsp;')
    return str


def html_graph_prefix(fh):
    fh.write("<html>\n")
    fh.write("<head>\n<style type=\"text/css\">\n<!--\n")
    fh.write("body { font-size: 18pt }\n")
    fh.write("table { font-size: 18pt; margin-left:20pt; }\n")
    fh.write(".user { background-color: lightblue; }\n")
    fh.write(".closure { background-color: pink;  }\n")
    fh.write(".user-inverted { background-color: lightyellow; }\n")
    fh.write(".closure-inverted { background-color: lightyellow; }\n")
    fh.write(".nocell { background-color: lightgrey; }\n")
    fh.write(".cycle { font-weight: bold; font-size: 18pt }\n")
    fh.write("-->\n</style>\n</head>\n")
    fh.write("<body>\n\n")
