#!/bin/csh -f

# ==============================================================================
# build_ttk_release.sh
# ==============================================================================
#
# Build a TTK distribution from the CVS repository. It builds the
# distribution from the most recently committed files. The script
# takes no argument, specific behaviour is determined by setting user
# option (see below).
#
# After execution of this script an archive ttk-VERSION-PLATFORM.tar.gz 
# will have been created in this directory.
#
# This script should be called from the directory it is in.
#
# ==============================================================================



# ============================= BUILD OPTIONS ===================================

# RELEASE_VERSION is used to give a version number to the release. Use
# `date +%Y%m%d` to use the current date as a version number.
set RELEASE_VERSION = `date +%Y%m%d`
set RELEASE_VERSION = '1.0'

# When BUILD_TAGGER is set to 1, the TreeTagger will be included in
# the release, this needs to be set to 0 for an official release
# (since we cannot redistribute the TreeTagger). If a tagger is built,
# then the PLATFORM variable needs to be set to osx or linux (windows
# not yet supported). The PLATFORM variable is ignored when no tagger
# is built.
set BUILD_TAGGER = 0
set PLATFORM = 'linux'

# TMP_DIR is used as a temporary directory and workspace for building
# the release.
set TMP_DIR = "tmp_build_dir"


# TODO: allow the user to specify a CVS tag
# TODO: add validation for all parameters above?


# ======================== NO EDITS NEEDED BELOW THIS LINE =======================

# store script directory for later use
set SCRIPT_DIR = `pwd`

echo
echo ">> Building a TTK distribution with version number $RELEASE_VERSION"

#./build_ttk_checkout.sh $TMP_DIR
./build_ttk_setup.sh $RELEASE_VERSION $BUILD_TAGGER $PLATFORM $SCRIPT_DIR $TMP_DIR

echo ">> Done"
echo
