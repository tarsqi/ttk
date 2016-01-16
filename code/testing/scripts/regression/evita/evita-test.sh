# Run the simple Evita regression tests

# See 00-readme.txt for details on how to run this.


pipeline=PREPROCESSOR,EVITA

testing_dir_in=testing/scripts/regression/evita/data-in
testing_dir_out=testing/scripts/regression/evita/data-out
testing_dir_tmp=testing/scripts/regression/evita/data-tmp

function run_test () {

    echo "\nRunning Evita regression test on $testing_dir_in/evita-$1.xml"
    if [ -f "$testing_dir_tmp/evita-$1.xml" ]; then
	rm $testing_dir_tmp/evita-$1.xml
    fi
    python tarsqi.py --pipeline=$pipeline $testing_dir_in/evita-$1.xml $testing_dir_tmp/evita-$1.xml &> /dev/null 
    diff $testing_dir_out/evita-$1.xml $testing_dir_tmp/evita-$1.xml

}

run_test $1



