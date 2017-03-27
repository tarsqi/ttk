
This directory contains some shell scripts to run simple and coarse-grained
regression tests for Evita. It is not a replacement for the regression tests in
code/testing/regression.py, which tracks results on a number of cases where each
case is a sentence. These scripts do a glorified diff on the results of
processing an entire file against a baseline that was saved earlier.

Tests need to be run from the code directory.

First, if you have not done this already, you need to create the files where
future runs of Tarsqi are compared against:

   $ sh testing/scripts/regression/evita/setup.sh

To run scripts for data files:

   $ sh testing/scripts/regression/evita/run.sh <TEST_CASE>?

Here, TEST_CASE points at the name of the test case. Cases are in the data-in
directory and all look like evita-test-NAME.xml. Examples:

   $ sh testing/scripts/regression/evita/run.sh BE
   $ sh testing/scripts/regression/evita/run.sh OTHER

The argument is optional, if no argument is given all tests will run:

   $ sh testing/scripts/regression/evita/run.sh

If all the output you get is messages that Tarsqi is running, then the
regression test passed. In all other cases you will get to see missing file
error messages if Tarsqi threw an error or the output of the diff command if new
results differed from baseline results.

The output is compared to the baseline using compare.py, which abstracts away
from some differences. In the Evita case, it only compares <ng>, <vg> and
<EVENT> tags, which gets rid of the side effects that tests start failing after
a day because the DCT changes (the tarsqi default is the current date) and
therefore some TIMEX tags change as well. In addition, it does not insist that
identifiers are the same so missing one events does not result in a cascade of
mismatching events.

Note that if a slightly adapted version of this script were to be used for TIMEX
tags, then the problem with failures would return unless we use a fixed DCT.


TODO:

- Make it so that these scripts can run from any directory

- See if it makes sense for the setup script to be merged into evita-test.sh.
