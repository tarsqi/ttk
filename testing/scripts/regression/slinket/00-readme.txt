
This directory contains some shell scripts to run simple and coarse-grained
regression tests for Slinket. It is not a replacement for the regression tests
in code/testing/regression.py (which actually do not even have tests for SLinket
as of January 2016), which tracks results on a number of cases where each case
is a sentence. These scripts do a customized diff on the results of processing
an entire file against a baseline that was saved earlier.

Tests need to be run from the code directory.

First, if you have not done this already, you need to create the files where
future runs of Tarsqi are compared against:

   $ sh testing/scripts/regression/slinket/setup.sh

To run scripts for data files:

   $ sh testing/scripts/regression/slinket/run.sh

If all the output you get is messages that tests are running, then the
regression test passed. In all other cases you will get to see missing file
error messages if Tarsqi threw an error or the output of the diff command if new
results differed from baseline results.

The input data in for these test were taken by running Slinket on all Timebank
files and then selecting those files that had 2 or more ALINKs in them.


TODO:
- Make it so that these scripts can run from any directory
- See if it makes sense for the setup script to be merged into slinket-test.sh.
