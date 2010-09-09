#!/bin/csh -f

# Run regression test on the current code. Runs evita, slinket and s2t
# and compares output in test/current directories with a baseline
# using diff.

set baselinedir = baseline1

set begintime = `date +%s`

rm test/current/evita-out/*
rm test/current/slinket-out/*
rm test/current/s2t-out/*

python ttk.py test/current/pre-out test/current/evita-out test/current/slinket-out  test/current/s2t-out

set endtime =  `date +%s`

@ time_elapsed = $endtime - $begintime


echo
echo "STARTED  $begintime"
echo "ENDED    $endtime"
echo 
echo "TIME ELAPSED: $time_elapsed"
echo


echo diff test/$baselinedir/evita-out/ABC19980108.1830.0711 test/current/evita-out/ABC19980108.1830.0711
diff test/$baselinedir/evita-out/ABC19980108.1830.0711 test/current/evita-out/ABC19980108.1830.0711

echo diff test/$baselinedir/evita-out/APW19980626.0364 test/current/evita-out/APW19980626.0364
diff test/$baselinedir/evita-out/APW19980626.0364 test/current/evita-out/APW19980626.0364

echo diff test/$baselinedir/evita-out/CNN19980126.1600.1104 test/current/evita-out/CNN19980126.1600.1104
diff test/$baselinedir/evita-out/CNN19980126.1600.1104 test/current/evita-out/CNN19980126.1600.1104

echo diff test/$baselinedir/evita-out/wsj_0159_orig test/current/evita-out/wsj_0159_orig
diff test/$baselinedir/evita-out/wsj_0159_orig test/current/evita-out/wsj_0159_orig


echo

echo diff test/$baselinedir/slinket-out/ABC19980108.1830.0711 test/current/slinket-out/ABC19980108.1830.0711
diff test/$baselinedir/slinket-out/ABC19980108.1830.0711 test/current/slinket-out/ABC19980108.1830.0711

echo diff test/$baselinedir/slinket-out/APW19980626.0364 test/current/slinket-out/APW19980626.0364
diff test/$baselinedir/slinket-out/APW19980626.0364 test/current/slinket-out/APW19980626.0364

echo diff test/$baselinedir/slinket-out/CNN19980126.1600.1104 test/current/slinket-out/CNN19980126.1600.1104
diff test/$baselinedir/slinket-out/CNN19980126.1600.1104 test/current/slinket-out/CNN19980126.1600.1104

echo diff test/$baselinedir/slinket-out/wsj_0159_orig test/current/slinket-out/wsj_0159_orig
diff test/$baselinedir/slinket-out/wsj_0159_orig test/current/slinket-out/wsj_0159_orig


echo

echo diff test/$baselinedir/s2t-out/ABC19980108.1830.0711 test/current/s2t-out/ABC19980108.1830.0711
diff test/$baselinedir/s2t-out/ABC19980108.1830.0711 test/current/s2t-out/ABC19980108.1830.0711

echo diff test/$baselinedir/s2t-out/APW19980626.0364 test/current/s2t-out/APW19980626.0364
diff test/$baselinedir/s2t-out/APW19980626.0364 test/current/s2t-out/APW19980626.0364

echo diff test/$baselinedir/s2t-out/CNN19980126.1600.1104 test/current/s2t-out/CNN19980126.1600.1104
diff test/$baselinedir/s2t-out/CNN19980126.1600.1104 test/current/s2t-out/CNN19980126.1600.1104

echo diff test/$baselinedir/s2t-out/wsj_0159_orig test/current/s2t-out/wsj_0159_orig
diff test/$baselinedir/s2t-out/wsj_0159_orig test/current/s2t-out/wsj_0159_orig

