#!/bin/bash

# Example script on how to install the TreeTagger on OSX. The download, install
# and test variables let you determine what steps need to be taken. With the
# current defaults the only thing that happens is that a TreeTagger installation
# in treetagger will be tested with the test recommended by the TreeTagger
# website (http://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/).

# It is possible for the test to fail while the TreeTagger may still be used by
# TTK. This can be the case when you have an older version of Perl (for example
# version 5.12). The TreeTagger test in this file uses a Perl script named
# utf8-tokenize.perl which uses the regular expression \p{XPosixCntrl} was not
# yet available. If you want you can edit utf8-tokenize.perl and replace
# \p{XPosixCntrl} with \p{Cntrl}.

download=false
install=false
test=true

data_dir=http://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data

if [ ! -d treetagger ]; 
then
    mkdir treetagger
fi

cd treetagger

if [ $download = "true" ]; 
then
    curl -O $data_dir/tree-tagger-MacOSX-3.2.tar.gz
    curl -O $data_dir/tagger-scripts.tar.gz
    curl -O $data_dir/install-tagger.sh
    curl -O $data_dir/english-par-linux-3.2-utf8.bin.gz
fi

if [ $install = "true" ];
then
    sh install-tagger.sh
fi

if [ $test = "true" ];
then
    echo 'Hello world!' | cmd/tree-tagger-english 
fi
