# Run the simple Slinket regression tests

# Run this from the code directory. See 00-readme.txt for more details on this.


pipeline=PREPROCESSOR,EVITA,SLINKET

script_dir=testing/scripts/regression/slinket
testing_dir_in=testing/scripts/regression/slinket/data-in
testing_dir_out=testing/scripts/regression/slinket/data-out
testing_dir_tmp=testing/scripts/regression/slinket/data-tmp

function run_test () {

    echo "\nRunning Slinket regression test on $1"

    infile=$testing_dir_in/$1
    outfile=$testing_dir_tmp/$1
    basefile=$testing_dir_out/$1

    if [ -f "$outfile" ]; then
	rm $outfile
    fi
    #echo "python tarsqi.py --pipeline=$pipeline $infile $outfile &> /dev/null"
    python tarsqi.py --pipeline=$pipeline $infile $outfile &> /dev/null
    #echo "python $script_dir/compare.py $basefile $outfile"
    python $script_dir/compare.py $basefile $outfile

}


if [ "$#" -eq  "0" ]; then
    for infile in $testing_dir_in/*.xml;
    do
	basename=`basename $infile`
	run_test $basename
    done
 else
    run_test $1
 fi
