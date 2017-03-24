# Create baseline files for the Slinket regression tests

pipeline=PREPROCESSOR,EVITA,SLINKET

testing_dir_in=testing/scripts/regression/slinket/data-in
testing_dir_out=testing/scripts/regression/slinket/data-out

for infile in $testing_dir_in/*.xml;
do
    basename=`basename $infile`
    infile=$testing_dir_in/$basename
    outfile=$testing_dir_out/$basename
    echo "Creating new $outfile"
    if [ -f "$outfile" ]; then
	rm $outfile
    fi
    #echo "python tarsqi.py --pipeline=$pipeline $infile $outfile &> /dev/null "
    python tarsqi.py --pipeline=$pipeline $infile $outfile &> /dev/null 
done



