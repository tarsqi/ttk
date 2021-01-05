from __future__ import absolute_import
import pprint


def pp(stuff):
    pretty_printer = pprint.PrettyPrinter(indent=3)
    pretty_printer.pprint(stuff)
