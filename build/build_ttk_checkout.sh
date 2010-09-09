#!/bin/csh -f


set TMP_DIR = $1


if (-d $TMP_DIR) then
    echo ">> Warning: cleaning up temporary directory of previous distribution"
    rm -r $TMP_DIR
endif

mkdir $TMP_DIR
cd $TMP_DIR


echo ">> Checking out files from CVS"


echo "   cvs -Q checkout ttk/docs/manual"
cvs -Q checkout ttk/docs/manual

echo "   cvs -Q checkout ttk/docs/code"
cvs -Q checkout ttk/docs/code

#echo "   cvs -Q checkout ttk/docs/papers"
#cvs -Q checkout ttk/docs/papers

echo "   cvs -Q checkout ttk/code/*.py"
cvs -Q checkout ttk/code/tarsqi.py
cvs -Q checkout ttk/code/setup.py
cvs -Q checkout ttk/code/settings.txt
cvs -Q checkout ttk/code/modules.py
cvs -Q checkout ttk/code/stats.py
cvs -Q checkout ttk/code/make_documentation.py
cvs -Q checkout ttk/code/ttk_path.py
cvs -Q checkout ttk/code/gui.py

echo "   cvs -Q checkout ttk/code/data/in"
cvs -Q checkout ttk/code/data/in/RTE3
cvs -Q checkout ttk/code/data/in/simple-xml
cvs -Q checkout ttk/code/data/in/TimeBank

echo "   cvs -Q checkout ttk/code/components"
cvs -Q checkout ttk/code/components/__init__.py

echo "   cvs -Q checkout ttk/code/components/arglinker"
cvs -Q checkout ttk/code/components/arglinker

echo "   cvs -Q checkout ttk/code/components/blinker"
cvs -Q checkout ttk/code/components/blinker

echo "   cvs -Q checkout ttk/code/components/classifier"
cvs -Q checkout ttk/code/components/classifier

echo "   cvs -Q checkout ttk/code/components/common_modules"
cvs -Q checkout ttk/code/components/common_modules

echo "   cvs -Q checkout ttk/code/components/evita"
cvs -Q checkout ttk/code/components/evita

echo "   cvs -Q checkout ttk/code/components/gutime"
cvs -Q checkout ttk/code/components/gutime

echo "   cvs -Q checkout ttk/code/components/merging"
cvs -Q checkout ttk/code/components/merging

echo "   cvs -Q checkout ttk/code/components/preprocessing"
cvs -Q checkout ttk/code/components/preprocessing

echo "   cvs -Q checkout ttk/code/components/s2t"
cvs -Q checkout ttk/code/components/s2t

echo "   cvs -Q checkout ttk/code/components/slinket"
cvs -Q checkout ttk/code/components/slinket

echo "   cvs -Q checkout ttk/code/library"
cvs -Q checkout ttk/code/library/__init__.py
cvs -Q checkout ttk/code/library/forms.py
cvs -Q checkout ttk/code/library/patterns.py
cvs -Q checkout ttk/code/library/tarsqi_constants.py
cvs -Q checkout ttk/code/library/timeMLspec.py

echo "   cvs -Q checkout ttk/code/library/blinker"
cvs -Q checkout ttk/code/library/blinker

echo "   cvs -Q checkout ttk/code/library/evita"
cvs -Q checkout ttk/code/library/evita

echo "   cvs -Q checkout ttk/code/library/slinket"
cvs -Q checkout ttk/code/library/slinket

echo "   cvs -Q checkout ttk/code/library/s2t"
cvs -Q checkout ttk/code/library/s2t

echo "   cvs -Q checkout ttk/code/demo"
cvs -Q checkout ttk/code/demo

echo "   cvs -Q checkout ttk/code/docmodel/"
cvs -Q checkout ttk/code/docmodel/

echo "   cvs -Q checkout ttk/code/utilities"
cvs -Q checkout ttk/code/utilities



echo ">> Removing CVS directories"

rm -r ttk/CVS
rm -r ttk/*/CVS
rm -r ttk/*/*/CVS
rm -r ttk/*/*/*/CVS
rm -r ttk/*/*/*/*/CVS
rm -r ttk/*/*/*/*/*/CVS

