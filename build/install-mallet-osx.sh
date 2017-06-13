#!/bin/bash

# Example script on how to install MALLET on OSX. The download, install and test
# variables let you determine what steps need to be taken. With the current
# defaults the only thing that happens is that bin/mallet is run to print a list
# of commands. See http://mallet.cs.umass.edu/quick-start.php.

download=false
install=false
test=true

archive=http://mallet.cs.umass.edu/dist/mallet-2.0.8.tar.gz


if [ ! -d mallet ]; then mkdir mallet 
fi

cd mallet

if [ $download = "true" ]; then curl -O $archive
fi

if [ $install = "true" ]; then gunzip -c mallet-2.0.8.tar.gz | tar xp
fi

if [ $test = "true" ]; then mallet-2.0.8/bin/mallet --help 
fi
