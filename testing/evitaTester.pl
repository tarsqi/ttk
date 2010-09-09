#!/usr/bin/perl

# To call it:
#
# evitaTester.pl -k key_directory -t target_directory
#
# Optional modes: -mvs Only looking for nouns and verbs; disregarding states.
#                 -a Output differences between key and target directories

use Getopt::Std;

my %opts;

getopts('k:t:anpsmv', \%opts);
my $docs;
my $fpExtents;
my $correctExtents;
my $totalExtents;
my $fnExtents;
my %attScores;

die "need a key and a target" unless ($opts{k} && $opts{t});

if (-d $opts{k}){
    if (-d $opts{t}) {
        procDirs($opts{k}, $opts{t});
        printPRF();
        printAttributeScores();
    } else {die "key is a directory and target is a file";}
} else {
    if (-d $opts{t}){
        die "key is a file and target is a directory";
    } else {
        scorePair($opts{k}, $opts{t});
        printPRF();
        printAttributeScores();
    }
}


sub procDirs {
    my $keyDir = shift;
    my $targDir = shift;
    
    
    
    opendir TARGDIR, $targDir or die "can't find targ directory";

    my @targFiles = readdir(TARGDIR);

    for (@targFiles) {
        unless (/^\./) {
            my $baseName = $_;
            my $targFileName = "$targDir\/$baseName";
            $baseName =~ s/\.cnk\.events//;
            $baseName =~ s/\.tml//;
            #my $keyFileName = "$keyDir\/$baseName.tml";  
            print "DOC:\t"; print my $keyFileName = "$keyDir\/$baseName.tml"; print "\n";
            if (isGoodFile($keyFileName)) {
                if (isGoodFile($targFileName)){
                    scorePair($keyFileName, $targFileName);
                } else {print "MISSING FILE: $targFileName\n";}
            } else {print "MISSING FILE: $keyFileName\n";} 
        }
    }
}

sub isGoodFile {
    $fileName = shift;
    return (-e $fileName && -s $fileName > 0 );
}

sub getMatches {
    my $hashRef = shift;
    my %matches;
    my %FPs;
    for (keys %{$hashRef}) {
        if ($keyEvents->{$_}) {
            $matches{$_} = $hashRef->{$_};
        } else {
            $FPs{$_} = $hashRef->{$_} unless $states{$_}
        }
    }
    return (\%matches, \%FPs);  
}

sub getFNs {
    my %FNs;
    for (keys %{$keyEvents}){
        unless ($targEvents->{$_} || $states{$_}){
            $FNs{$_} = $keyEvents->{$_};
        }
    }
    return \%FNs;
}


sub procMatches {
    my $fileName = shift;
    my $matches = shift;
    my $FPs = shift;
    my $shift = shift;
    my $FNs = getFNs();
    my @filepath = split /\//, $fileName;
    my $fileName = $filepath[-1];
    $docs++;
    $correctExtents += keys %{$matches};
    $totalExtents += keys %{$keyEvents};
    $fpExtents += keys %{$FPs};
    $fnExtents += keys %{$FNs};
    for (keys %{$matches}) {
        my $keyAtts = $keyEvents->{$_};
        my $targAtts = $targEvents->{$_};
        my $keyInstAtts = $keyInstances->{$keyAtts->{'eid'}};
        my $targInstAtts = $targInstances->{$targAtts->{'eid'}};
        $attScores{'class'}++ if ($targAtts->{'class'} eq $keyAtts->{'class'});
        for ('tense', 'aspect', 'pos', 'polarity', 'modality') {#
            if (($targInstAtts->{$_} eq $keyInstAtts->{$_}) ||
                ($targInstAtts->{$_} eq 'POS' && $keyInstAtts->{$_} == 0)){
                    $attScores{$_}++; 
            } else {
                print "$fileName\tATT:\t$_\t$targAtts->{'eid'}\t$keyInstAtts->{$_}\t$targInstAtts->{$_}\n" if $opts{a};
            }
        }
    }
    if ($opts{n}) {
        while (my ($k, $v) = each %{$FNs}){
            my ($b, $e) = split(":", $k);
            my $b1 = $targIndex->{$b+$shift};
            my $e1 = $targIndex->{($e-1)+$shift};
            my $b0 = $b1 - 30;
            my $e0 = $e1 + 30;
            my $errString = substr($targFile, $b0, $b1-$b0);
            $errString .= "[";
            $errString .= substr($targFile, $b1, ($e1-$b1)+1);
            $errString .= "]";
            $errString .= substr($targFile, $e1+1, $e0-$e1);
            print "FN:\t";
            print $v->{'eid'};
            print "\t$errString\n";
        }
    }
    if ($opts{p}){
        while (my ($k, $v) = each %{$FPs}){
            my ($b, $e) = split(":", $k);
            my $b1 = $targIndex->{$b+$shift};
            my $e1 = $targIndex->{($e-1)+$shift};
            my $b0 = $b1 - 30;
            my $e0 = $e1 + 30;
            my $errString = substr($targFile, $b0, $b1-$b0);            
            $errString .= "[";
            $errString .= substr($targFile, $b1, ($e1-$b1)+1);            
            $errString .= "]";
            $errString .= substr($targFile, $e1+1, $e0-$e1);            
            print "FP:\t";
            print $v->{'eid'};
            print "\t$errString\n";
        }
    }
}


sub inPos{
    my ($begin, undef) = split(":", shift);
    my $beginOffset = $targIndex->{$begin};
    my $lexString = substr($targFile, $beginOffset-20, 20);
    if ($lexString =~ /pos="VB.?"/ && $opts{v}) {
        return 1;
    } elsif ($lexString =~ /pos="NNS?"/ && $opts{m}) {
        return 1;
    } else { return 0}
}

sub scorePair{
    my $keyFileName = shift;
    my $targFileName = shift;
    local %states;
    local ($keyEvents, $keyInstances, $keyFile) = getTagData($keyFileName);
    local ($targEvents, $targInstances, $targFile) = getTagData($targFileName);
    local $keyIndex = indexText($keyFile);
    local $targIndex = indexText($targFile);
    
    if ($opts{v} || $opts{m}){
        for (keys %{$keyEvents}){
            delete $keyEvents->{$_} unless inPos($_);
        }
        for (keys %{$targEvents}){
            delete $targEvents->{$_} unless inPos($_);
        }
    }


    if ($opts{s}){
        for (keys %{$keyEvents}){
            my $class = $keyEvents->{$_}->{'class'};
            if ($class eq 'STATE' || $class eq 'I_STATE'){
                $states{$_} = 1 unless delete $targEvents->{$_};
                delete $keyEvents->{$_};
            }
        }
        for (keys %{$targEvents}){
            my $class = $targEvents->{$_}->{'class'};
            if ($class eq 'STATE' || $class eq 'I_STATE'){
                $states{$_} = 1 unless delete $keyEvents->{$_};
                delete $targEvents->{$_};
            }
        }
    }

    my ($gMatches, $gFPs) = getMatches($targEvents);
    if (keys %{$gMatches} > 0){
        procMatches($targFileName,$gMatches, $gFPs);
    } else {
        for (keys %{$targEvents}) {
            my ($x, $y) = split(/:/, $_);
            my $v = $targEvents->{$_};
            delete $targEvents->{$_};
            my $k = join(":", ($x+1, $y+1));
            $targEvents->{$k} = $v;
        }
        ($gMatches, $gFPs) = getMatches($targEvents);
        if (keys %{$gMatches} > 0){
            procMatches($targFileName, $gMatches, $gFPs, -1)
        } else {
            procMatches($targFileName, $gMatches, $gFPs);
            print "NO MATCHING EVENTS: $targFileName\n";
        }
    }
}


sub getTagData {

    my $inFileName = shift;

    my $outFileName = $inFileName;

    $outFileName =~ s/\///g;

    $outFileName = '/tmp/'.$outFileName;
    
    my $ptfFileName = "$outFileName.EVENT.tag";
    my $file;
    {
    local $/;
    open FILE, $inFileName or die "can't open inFile";

    $file = <FILE>;
    }
    $file =~ s/\n//g;

    open OUT, ">$outFileName" or die "can't open $outFileName";
    print OUT $file;
    system('/home/j/corpuswork/tools/AlembicChunker/bin/sgm2ptf -q -i '.$outFileName.' -s /home/j/corpuswork/tools/AlembicChunker/awbEvents.tsd 2> /dev/null') == 0 or die "problem making ptf";

    eval {open PTF, $ptfFileName;};
    print "NO EVENTS: $inFileName\n" if $@;

    my @ptfArray = <PTF>;
    
    my ($eventHashRef, $instanceHashRef) = parsePtf(\@ptfArray);

    close PTF;

    unlink <$outFileName*> if $outFileName;

    return ($eventHashRef, $instanceHashRef, $file);

}


sub indexText {
    my $file = shift;
    my %hash;
    my $allCount;
    my $textCount;
    my $keepIt = 1;
    for (split('', $file)){
        $keepIt = 0 if /</;
        $hash{$textCount} = $allCount if $keepIt;
        $textCount++ if $keepIt;
        $allCount++;
        $keepIt = 1 if />/;
    }
    return \%hash;
}
    

    
sub parsePtf {
    my $ptfArrayRef =  shift;
    my %eventHash;
    my %instanceHash;
    for (@{$ptfArrayRef}){
        next if /^([A-Z]|\s)/;
        my @bits = split(' ', $_);
        my ($startX, $endX) = @bits[2,3];
        my $start = join(' ', @bits[4..scalar(@bits)-1]);
        my %atts;
        while ($start =~ /([^ ]+?)=\"(.+?)\"/g) {
            $atts{$1} = $2;
        }
        if ($endX == -999){
            $instanceHash{$atts{'eventID'}} = \%atts;
        }else{
            $eventHash{"$startX:$endX"} = \%atts;
        }
    }
    return (\%eventHash, \%instanceHash);
}


sub printPRF {
warn "\nNO STATES CONSIDERED\n" if $opts{s};
warn "\nNOMINALS\n" if $opts{m};
warn "\nVERBS\n" if $opts{v};


if ($correctExtents) {
    my $targEventCount = ($correctExtents + $fpExtents);
    warn "\n====================\n";
    warn "Docs:\t$docs\n";
    warn "Events in key:\t$totalExtents\n";
    warn "Events in target:\t$targEventCount\n";
    warn "Correct:\t$correctExtents\n";
    
    my $recall = $correctExtents / ($correctExtents + $fnExtents); 
    my $precision = $correctExtents / $targEventCount;
    my $F1 = (2 * ($precision * $recall)) / ($precision + $recall); 


    $recall = sprintf '%.2f', ($recall * 100);
    $precision = sprintf '%.2f', ($precision * 100);
    $F1 = sprintf '%.2f', ($F1 * 100);

    warn "\n=====EXTENTS==========\n";

    warn "P:\t$precision\%\n";
    warn "R:\t$recall\%\n";
    warn "F1\t$F1\%\n";
} else {warn "NO CORRECT EVENTS\n";}

}

sub printAttributeScores {
    if ($correctExtents) {
    warn "\n=====ATTRIBUTES=====\n";
    while (my ($k, $v) = each %attScores) {
        my $value = sprintf '%.2f', (($v / $correctExtents) * 100);
        warn "$k\t$value\%\n";
    }
}
}
