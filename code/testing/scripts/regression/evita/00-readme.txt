
This directory contains some shell scripts to run simple and coarse-grained
regression tests. It is not a replacement for code/testing/regression.py, which
tracks results on a number of cases where each case is a sentence. These scripts
do a diff on the results of processing an entire file against a baseline that
was saved earlier.

Tests need to be run from the code directory.

First, if you have not done this already, you need to create the files where
future runs of Tarsqi are compared against:

   $ sh testing/scripts/regression/evita/setup-evita-tests.sh

To run scripts for data files:

   $ sh testing/scripts/regression/evita/evita-test-BE.sh
   $ sh testing/scripts/regression/evita/evita-test-OTHER.sh

To run all scripts:

   $ sh testing/scripts/regression/evita/evita-test-ALL.sh

If all the output you get is messages that Tarsqi is running or that results are
compared, then the regression test passed. In all other cases you will get to
see missing file error messages if Tarsqi threw an error or the output of the
diff command if new results differed from old results.

Note that most, if not all, of these tests are guaranteed to fail after a about
week. This is because Tarsqi uses the current date for processing, which is used
for resolving the normalized value of some time expressions. Jut rerun the
setup-evita-tests.sh scripts again to recreate the baseline.


TODO:

- Only BE and OTHER are ready, add the others.

- There is a lot of redundancy between the shell scripts, use one script that
  takes an argument to pick out the data set (or sets).

- Make it so that these scripts can run from any directory
