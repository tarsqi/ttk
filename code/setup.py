"""

This module sets up the the MaxEnt Classifier for several platforms
and changes the settings.txt file.

Usage:

    python setup.py [flag=value]*

A platform flag is retrieved from the environment if no fragment is
specified, supported values are 'linux2' and 'darwin'. This flag is
needed to determine what classifier executable to use. This script
will install the correct version given this setting. Currently, only
Mac OSX and Linux are supported, Windows support, with a win32 flag,
will follow asap.

All other flags result in adding or changing lines to the settings.txt
file. That file is read when the toolkit starts up and all its
settings are added to the processing parameters. The only settings
that make sense are those processing parameters that are understood by
the toolkit, see the manual for a listing.

If settings.txt does not have a line like with a perl setting then it
will make a guess as to where the Perl executable lives. In most
cases, it will add

    perl=perl

but if setup.py can find an ActivePerl distribution it will use the
path to it, for example:

    perl=/usr/local/ActivePerl-5.8/bin/perl

Specifying a Perl flag overrides this.

"""

import sys
import os
import string

from ttk_path import TTK_ROOT
from utilities.file import read_settings, write_settings
from library.tarsqi_constants import TRAP_ERRORS, EXTENSION, PIPELINE
from library.tarsqi_constants import CONTENT_TAG, REMOVE_TAG, PLATFORM, PERL

CLASSIFIER_DIR = os.path.join(TTK_ROOT, 'components', 'classifier')

USAGE = "python setup.py [flag=value]*"

settings = {}

KNOWN_FLAGS = [ TRAP_ERRORS, EXTENSION, PIPELINE,
                CONTENT_TAG, REMOVE_TAG, PLATFORM, PERL ]


def setup_classifier(platform):
    """Sets up the Classifier. It first cleans out old binaries and
    then unpacks new ones appropriate to the platform. This method
    assumes that the classifier directory contains files
    mxtest.opt.PLATFORM and mxtrain.opt.PLATFORM."""
    os.chdir(CLASSIFIER_DIR)
    for file in ('mxtest.opt', 'mxtrain.opt'):
        if os.path.exists(file):
            os.remove(file)
    if platform == 'darwin':
        os.system("cp mxtest.opt.osx mxtest.opt")
        os.system("cp mxtrain.opt.osx mxtrain.opt")
        print "\nClassifier is set up for Darwin"
    elif platform == 'linux2':
        os.system("cp mxtest.opt.linux mxtest.opt")
        os.system("cp mxtrain.opt.linux mxtrain.opt")
        print "\nClassifier is set up for Linux"
    else:
        print "\nWarning: platform %s is not supported" % platform
    os.chdir(TTK_ROOT)
    

def add_perl_path(settings):
    """Add a Perl path to the settings if there wasn't one yet."""
    if not settings.has_key(PERL):
        settings[PERL] = 'perl'
        path = get_active_state_perl()
        if path:
            settings[PERL] = path

def get_active_state_perl():
    """Return None or the path to the ActivePerl executable if it can find
    one. Looks for a directory starting with 'ActivePerl' inside of
    '/usr/local'. This method is designed to work only for OSX."""
    # NOTE: check whether this fails gracefully on Windows
    usr_local = os.path.join('/usr', 'local')
    if os.path.isdir(usr_local):
        for file in os.listdir(usr_local):
            if file.startswith('ActivePerl'):
                return os.path.join(usr_local, file, 'bin', 'perl')
    return None
        



if __name__ == '__main__':

    args = sys.argv[1:]

    # reading settings from environment and parameters
    settings[PLATFORM] = sys.platform
    for arg in args:
        try:
            (flag, value) = map(string.strip, arg.split('='))
            if flag in KNOWN_FLAGS:
                settings[flag] = value
            else:
                print "WARNING: ignoring unknown flag", flag
        except ValueError:
            sys.exit("\nUnexpected argument.\nUsage: %s\n" % USAGE)
    add_perl_path(settings)

    # set up the classifier
    setup_classifier(settings[PLATFORM])
    
    # update settings file
    all_settings = read_settings('settings.txt')
    all_settings.update(settings)
    write_settings(all_settings, 'settings.txt')

    print "\nCurrent default settings:\n"
    for flag in all_settings:
        print "  %-15s %s" % (flag, all_settings[flag])
    print
