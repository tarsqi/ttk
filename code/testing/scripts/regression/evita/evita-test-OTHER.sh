pipeline=PREPROCESSOR,EVITA

testing_dir_in=testing/scripts/regression/evita/data-in
testing_dir_out=testing/scripts/regression/evita/data-out
testing_dir_tmp=testing/scripts/regression/evita/data-tmp

rm $testing_dir_tmp/evita-OTHER.xml

echo "\nRunning Tarsqi on $testing_dir_in/evita-OTHER.xml"
python tarsqi.py --pipeline=$pipeline $testing_dir_in/evita-OTHER.xml $testing_dir_tmp/evita-OTHER.xml &> /dev/null 

echo "  comparing result to $testing_dir_out/evita-OTHER.xml"
diff $testing_dir_out/evita-OTHER.xml $testing_dir_tmp/evita-OTHER.xml
