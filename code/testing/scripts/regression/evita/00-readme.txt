
This directory contains some shell scripts to run simple and coarse-grained
regression tests. It is not a replacement for code/testing/regression.py, which
tracks results on a number of cases where each case is a sentence. These scripts
do a diff on the results of processing an entire file against a baseline that
was saved earlier.

We now only have regressions tests for Evita.

Tests need to be run from the code directory.

First, if you have not done this already, you need to create the files where
future runs of Tarsqi are compared against:

   $ sh testing/scripts/regression/evita/setup-evita-tests.sh

To run scripts for data files:

   $ sh testing/scripts/regression/evita/evita-test.sh <TEST_CASE>?

Here, TEST_CASE points at the name of the test case. Cases are in the data-in
directory and all look like evita-test-NAME.xml. Examples:

   $ sh testing/scripts/regression/evita/evita-test.sh BE
   $ sh testing/scripts/regression/evita/evita-test.sh OTHER

The argument is optional, if no argument is given all tests will run:

   $ sh testing/scripts/regression/evita/evita-test.sh

If all the output you get is messages that Tarsqi is running, then the
regression test passed. In all other cases you will get to see missing file
error messages if Tarsqi threw an error or the output of the diff command if new
results differed from baseline results.

Note that most, if not all, of these tests are guaranteed to fail after a about
week. This is because Tarsqi uses the current date for processing, which is used
for resolving the normalized value of some time expressions. Just rerun the
setup-evita-tests.sh scripts again to recreate the baseline.

Update: the former is not true for evita-test.sh anymore since we do not use
diff to compare results anymore, however, when GUTime or BTime is going to be
tested this way the issue will return.

TODO:

- Make it so that these scripts can run from any directory

- See if it makes sense for the setup script to be merged into evita-test.sh.
