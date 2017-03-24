pipeline=PREPROCESSOR,EVITA

testing_dir_in=testing/scripts/regression/evita/data-in
testing_dir_out=testing/scripts/regression/evita/data-out

for name in BE BECOME COMPLEX CONTINUE DO GOING HAVE KEEP OTHER USED
do
    infile=$testing_dir_in/evita-$name.xml
    outfile=$testing_dir_out/evita-$name.xml
    echo "Creating new $outfile"
    if [ -f "$outfile" ]; then
	echo "  removing current version $outfile"
	rm $outfile
    fi
    python tarsqi.py --pipeline=$pipeline $infile $outfile &> /dev/null 
done
