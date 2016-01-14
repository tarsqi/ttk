
This directory contains some shell scripts to run simple and coarse-grained
regression tests. It is not a replacement for code/testing/regression.py, which
tracks results on a number of cases where each case is a sentence. These script
do a diff on the results of processing an entire file at to different times.

Tests need to be run from the code directory.

To run scripts for data files:

   $ sh testing/scripts/regression/evita/evita-test-BE.sh
   $ sh testing/scripts/regression/evita/evita-test-OTHER.sh

To run all scripts:

   $ sh testing/scripts/regression/evita/evita-test-ALL.sh

If all the output you get is messages that Tarsqi is running or that results are
compared, then the regression test passed. In all other cases you will get to
see missing file error messages if Tarsqi threw an error or the output of the
diff command if new results differed from old results.


TODO:

- We need something like an initiate script, which sets up the files relative to
  which regression is measured. This can also be run when system behaviour has
  changed.

- Only BE and OTHER are ready, add the others.

- There is a lot of redundancy between the shell scripts, use one script that
  takes an argument to pick out the data set (or sets).
