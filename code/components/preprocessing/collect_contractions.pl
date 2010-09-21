
# Collecting contractions from a few lists taken from the web. used to created
# contractions.txt


open IN1, "contractions1.txt";
open IN2, "contractions2.txt";
open IN3, "contractions3.txt";

%CONTRACTIONS = ();

while(<IN1>) {
    /(\S+) \t(.*)/;
    print "1: <$1> \t $2\n";
    $CONTRACTIONS{lc $1} = $2;
}


while(<IN2>) {
    if (/(\S+) --- (.*) ---/) {
        if (! $CONTRACTIONS{lc $1}) {
            print "2: <$1>\t $2\n";
            $CONTRACTIONS{lc $1} = $2;
        }
    }
}

foreach $c ( split(',',<IN3>)) {
    $c =~ s/ +//;
    if (! $CONTRACTIONS{lc $c}) {
        print "3: <$c>\n";
        $CONTRACTIONS{lc $c} = 1;
    }
}


foreach $c (sort keys %CONTRACTIONS) {
    if ($c =~ /n't/) {
        push @negative, $c; }
    else {
        push @positive, $c; }
}

print "\n\n";
foreach $x (@positive) {
    print "<$x> \t [$CONTRACTIONS{$x}]\n"; }

print "\n\n";
foreach $x (@negative) {
    print "<$x> \t [$CONTRACTIONS{$x}]\n"; }
