#!/bin/csh -f

set RELEASE_VERSION = $1
set BUILD_TAGGER = $2
set PLATFORM = $3
set SCRIPT_DIR = $4
set TMP_DIR = $5


echo ">> Completing directory structure"
cd $TMP_DIR
mkdir ttk/code/data/in/User
mkdir ttk/code/data/tmp
mkdir ttk/code/data/out
mkdir ttk/code/data/display
mkdir ttk/code/data/logs

echo ">> Removing unneeded files"
rm ttk/code/data/in/RTE3/rte3-02{6,7,8,9}.xml
rm ttk/code/data/in/RTE3/rte3-03?.xml
rm ttk/code/data/in/RTE3/rte3-04?.xml
rm ttk/code/data/in/RTE3/rte3-050.xml
rm ttk/code/stats*

if $BUILD_TAGGER then
    echo ">> Installing tagger for $PLATFORM"
	cd $SCRIPT_DIR
	cd ../../../resources
	./install.sh $SCRIPT_DIR/$TMP_DIR tagger $PLATFORM
endif

echo ">> Adding Tango"
cd $SCRIPT_DIR
cd ../../../resources
./install.sh $SCRIPT_DIR/$TMP_DIR/ttk tango


echo ">> Creating archive"
cd $SCRIPT_DIR/$TMP_DIR
set VERSION = $RELEASE_VERSION
if $BUILD_TAGGER then
    set VERSION = $RELEASE_VERSION-$PLATFORM
endif

mv ttk ttk-$VERSION
tar cfp ttk-$VERSION.tar ttk-$VERSION/*
gzip ttk-$VERSION.tar


echo ">> Cleaning up"

cd $SCRIPT_DIR
mv $TMP_DIR/ttk-$VERSION.tar.gz .
rm -r $TMP_DIR

