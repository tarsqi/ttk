# Run the simple Evita regression tests

# Run this from the code directory. Without argument it runs all tests, with an
# argument just the one picked out by it. See 00-readme.txt for more details on
# this.


pipeline=PREPROCESSOR,EVITA

script_dir=testing/scripts/regression/evita
testing_dir_in=testing/scripts/regression/evita/data-in
testing_dir_out=testing/scripts/regression/evita/data-out
testing_dir_tmp=testing/scripts/regression/evita/data-tmp

function run_test () {

    echo "\nRunning Evita regression test on $testing_dir_in/evita-$1.xml"
    if [ -f "$testing_dir_tmp/evita-$1.xml" ]; then
	rm $testing_dir_tmp/evita-$1.xml
    fi
    python tarsqi.py --pipeline=$pipeline $testing_dir_in/evita-$1.xml $testing_dir_tmp/evita-$1.xml &> /dev/null 
    python $script_dir/compare.py $testing_dir_out/evita-$1.xml $testing_dir_tmp/evita-$1.xml

}


if [ "$#" -eq  "0" ]; then
    run_test BE
    run_test BECOME
    run_test COMPLEX
    run_test CONTINUE
    run_test DO
    run_test GOING
    run_test HAVE
    run_test KEEP
    run_test OTHER
    run_test USED
 else
    run_test $1
 fi



