
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

   $ sh testing/scripts/regression/evita/evita-test.sh <TEST_CASE>

Here, TEST_CASE points at the name of the test case. Cases are in the data-in
directory and all look like evita-test-NAME.xml. Examples:

   $ sh testing/scripts/regression/evita/evita-test.sh BE
   $ sh testing/scripts/regression/evita/evita-test.sh OTHER

To run all scripts:

   $ sh testing/scripts/regression/evita/evita-test-ALL.sh

If all the output you get is messages that Tarsqi is running or that results are
compared, then the regression test passed. In all other cases you will get to
see missing file error messages if Tarsqi threw an error or the output of the
diff command if new results differed from old results.

Note that most, if not all, of these tests are guaranteed to fail after a about
week. This is because Tarsqi uses the current date for processing, which is used
for resolving the normalized value of some time expressions. Just rerun the
setup-evita-tests.sh scripts again to recreate the baseline.


TODO:

- Make it so that these scripts can run from any directory

- Merge evita-test.sh and evita-test-ALL.sh, where the first script will
  consider not having an argument as a license to run all tests. Similarly, the
  setup script might be able to merged in as well.
