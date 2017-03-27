"""Module containing simple file utilities."""

import os
import pickle


def file_contents(filename):
    """Same as file_contents_as_string."""
    return file_contents_as_string(filename)


def file_contents_as_string(filename):
    """Returns the contents of a file as a string."""
    f = open(filename, 'r')
    content = '.'.join(f.readlines())
    f.close()
    return content


def file_contents_as_list(filename):
    """Returns the contents of a file as a list."""
    f = open(filename, 'r')
    content = f.readlines()
    f.close()
    return content


def write_text_to_file(text, filename):
    """Write a string to a file, overwriting an existing file. Takes a string and
    an absolute path as input.  Returns True if succesful, False otherwise."""
    try:
        f = open(filename, 'w')
        f.write(text)
        f.close()
        return True
    except:
        return False


def open_pickle_file(fname):
    """Return the contents of a pickle file."""
    with open(fname, 'r') as fh:
        return pickle.load(fh)


def read_config(filename):
    """Read the content of filename and put flags and values in a
    dictionary. Each line in the file is either an empty line, a line starting
    with '#' or an attribute-value pair separated by a '=' sign. Returns the
    dictionary."""
    file = open(filename, 'r')
    config = {}
    for line in file:
        line = line.strip()
        if not line:
            continue
        if line.startswith('#'):
            continue
        (flag, value) = [s.strip() for s in line.split('=')]
        config[flag] = value
    file.close()
    return config
