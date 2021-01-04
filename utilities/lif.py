"""lif.py

Interface to the LAPPS Interchance Format and to the LAPPS Data container.

Contains code to:

- Read JSON-LD strings for containers and LIF objects
- Export Containers and LIF objects to JSON-LD strings

To read and write a data container:

>>> container = Container(infile)
>>> container.write(outfile, pretty=True)

To read and write a LIF object:

>>> lif = LIF(infile)
>>> lif.write(outfile, pretty=True)

Normaly there would be some manipulation of the LIF object between reading and
writing, most typically by adding views.

On the command line:

$ python lif.py --container INFILE OUTFILE
$ python lif.py --lif INFILE OUTFILE

Example input files are in ../data/in/lif.

"""

from __future__ import absolute_import
from __future__ import print_function
import sys
import codecs
import json
import subprocess
from six.moves import range


class LappsObject(object):

    def __init__(self, json_file, json_string, json_object):
        if json_file is not None:
            self.json_string = codecs.open(json_file).read()
            self.json_object = json.loads(self.json_string)
        elif json_string is not None:
            self.json_string = json_string
            self.json_object = json.loads(self.json_string)
        elif json_object is not None:
            self.json_string = None
            self.json_object = json_object

    def write(self, fname=None, pretty=False):
        json_obj = self.as_json()
        if pretty:
            s = json.dumps(json_obj, sort_keys=True, indent=4, separators=(',', ': '))
        else:
            s = json.dumps(json_obj)
        fh = sys.stdout if fname is None else codecs.open(fname, 'w')
        fh.write(s + "\n")


class Container(LappsObject):

    def __init__(self, json_file=None, json_string=None, json_object=None):
        LappsObject.__init__(self, json_file, json_string, json_object)
        self.discriminator = self.json_object['discriminator']
        self.payload = LIF(json_object=self.json_object['payload'])
        self.parameters = self.json_object.get('parameters', {})

    def as_json(self):
        return {"discriminator": self.discriminator,
                "parameters": self.parameters,
                "payload": self.payload.as_json()}


class LIF(LappsObject):

    def __init__(self, json_file=None, json_string=None, json_object=None):
        LappsObject.__init__(self, json_file, json_string, json_object)
        self.context = "http://vocab.lappsgrid.org/context-1.0.0.jsonld"
        self.metadata = None
        self.text = Text(self.json_object['text'])
        self.views = []
        for v in self.json_object['views']:
            self.views.append(View(v))

    def as_json(self):
        d = {"@context": self.context,
             "metadata": {},
             "text": self.text.as_json(),
             "views": [v.as_json() for v in self.views]}
        return d

    def as_json_string(self):
        return json.dumps(self.as_json(), sort_keys=True, indent=4, separators=(',', ': '))

    def has_tarsqi_view(self):
        tok = "http://vocab.lappsgrid.org/Token"
        for view in self.views:
            contains = view.metadata['contains']
            if tok in contains and contains[tok].get("producer") == "TTK":
                return True
        return False

    def add_tarsqi_view(self, tarsqidoc):
        view = View()
        view.id = self._get_new_view_id()
        view.metadata["contains"] = {
            "http://vocab.lappsgrid.org/Token": {"producer": "TTK"},
            "http://vocab.lappsgrid.org/Token#pos": {"producer": "TTK"},
            "http://vocab.lappsgrid.org/Sentence": {"producer": "TTK"},
            "http://vocab.lappsgrid.org/Paragraph": {"producer": "TTK"},
            "http://vocab.lappsgrid.org/NounChunk": {"producer": "TTK"},
            "http://vocab.lappsgrid.org/VerbChunk": {"producer": "TTK"},
            "http://vocab.lappsgrid.org/Event": {"producer": "TTK"},
            "http://vocab.lappsgrid.org/TimeExpression": {"producer": "TTK"},
            "http://vocab.lappsgrid.org/TemporalRelation": {"producer": "TTK"}}
        for tag in tarsqidoc.tags.tags:
            anno = {"id": _get_id(tag), "@type": _get_type(tag),
                    "start": tag.begin, "end": tag.end, "features": {}}
            # TODO: the attributes for TemporalRelations need to be turned from
            # TTK attributes into LIF attributes, thi smay also need ot be done
            # for events and times
            for attr, val in tag.attrs.items():
                anno["features"][attr] = val
            if anno["@type"] is not None:
                view.annotations.append(Annotation(anno))
        self.views.append(view)

    def _get_new_view_id(self):
        ids = [view.id for view in self.views]
        for i in range(1, sys.maxsize):
            if "v%d" % i not in ids:
                return "v%d" % i


def _get_id(tag):
    identifier = tag.get_identifier()
    if identifier is not None:
        return identifier
    return IdentifierFactory.new_id(tag)


TYPE_MAPPINGS = {
    # for now ignoring Slinks and Alinks
    'docelement': 'Paragraph', 's': 'Sentence', 'lex': 'Token',
    'ng': 'NounChunk', 'vg': 'VerbChunk', 'EVENT': 'Event',
    'TIMEX3': 'TimeExpression', 'TLINK': 'TemporalRelation'}


def _get_type(tag):
    vocab = "http://vocab.lappsgrid.org"
    type_name = TYPE_MAPPINGS.get(tag.name)
    return "%s/%s" % (vocab, type_name) if type_name is not None else None


class Text(object):

    def __init__(self, json_obj):
        self.language = json_obj.get('language')
        self.value = json_obj.get('@value')

    def __str__(self):
        return "<Text lang=%s length=%d>" % (self.language, len(self.value))

    def as_json(self):
        d = {"@value": self.value}
        if self.language is not None:
            d["language"] = self.language
        return d


class View(object):

    def __init__(self, json_obj=None):
        self.id = None
        self.metadata = {}
        self.annotations = []
        if json_obj is not None:
            self.id = json_obj['id']
            self.metadata = json_obj['metadata']
            for a in json_obj['annotations']:
                self.annotations.append(Annotation(a))

    def __str__(self):
        return "<View id=%s with %d annotations>" % (self.id, len(self.annotations))

    def as_json(self):
        d = {"id": self.id,
             "metadata": self.metadata,
             "annotations": [a.as_json() for a in self.annotations]}
        return d

    def pp(self):
        print(self)
        for contains in self.metadata["contains"].keys():
            print('   ', contains)


class Annotation(object):

    def __init__(self, json_obj):
        self.id = json_obj['id']
        self.type = json_obj['@type']
        self.start = json_obj.get("start")
        self.end = json_obj.get("end")
        self.features = {}
        for feat, val in json_obj.get("features", {}).items():
            self.features[feat] = val

    def as_json(self):
        d = {"id": self.id, "@type": self.type, "features": self.features}
        if self.start is not None:
            d["start"] = self.start
        if self.start is not None:
            d["end"] = self.end
        return d


class IdentifierFactory(object):

    identifiers = {'docelement': 0, 's': 0, 'lex': 0, 'ng': 0, 'vg': 0}

    @classmethod
    def new_id(cls, tag):
        cls.identifiers[tag.name] += 1
        return "%s%d" % (tag.name, cls.identifiers[tag.name])


def compare(file1, file2):
    """Output file could have a very different ordering of json properties, so
    compare by taking all the lines, normalizing them (stripping space and commas)
    and sorting them."""
    lines1 = sorted(codecs.open(file1).readlines())
    lines2 = sorted(codecs.open(file2).readlines())
    with codecs.open("comp1", 'w') as c1, codecs.open("comp2", 'w') as c2:
        c1.write("\n".join([l.strip().rstrip(',') for l in lines1]))
        c2.write("\n".join([l.strip().rstrip(',') for l in lines2]))
    subprocess.call(['echo', '$ ls -al comp?'])
    subprocess.call(['ls', '-al', "comp1"])
    subprocess.call(['ls', '-al', "comp2"])
    subprocess.call(['echo', '$ diff', 'comp1', 'comp2'])
    subprocess.call(['diff', 'comp1', 'comp2'])


if __name__ == '__main__':

    input_type, infile, outfile = sys.argv[1:4]

    if input_type == '--lif':
        lapps_object = LIF(infile)
    elif input_type == '--container':
        lapps_object = Container(infile)

    # doesn't print this quite as I like it, for a view it first does the
    # annotations, then the id and then the metadata
    lapps_object.write(outfile, pretty=True)

    # test by comparing input and output
    compare(infile, outfile)
