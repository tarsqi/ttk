#!/usr/bin/perl -w

# Wrapper script for TimeTag.pl and TempEx, very loosely based on
# GUTime-Evita.pl Seok Bae Jang - sbj3@georgetown.edu (June 2005)

# TempEx cannot deal with other tags than s and lex, so all other tags
# are stripped. This script does not attempt to put them back in,
# leaving that task to the Python code of the Tarsqi toolkit.

# 12/01/08 (MV)
#
# Stripped away a lot of the unused code (ExDateTime for
# example). After this, the following base functionality remains:
#
# 1. input is an xmltree rooted in <fragment> with s, lex and
#    chunktags ( and potentially others as well)
# 2. parse options (-dct DATE -t fragment)
# 3. get DCT from options or current date
# 4. get the boy (between the fragment tags)
# 5. clean all tags from the body except s and lex
# 6. save body in xml file rooted in DOC with a DATE_TIME tag
# 7. run TimeTag and postTempex
# 8. remove DOC and DATE_TIME and save in new doc rooted in fragment
#
# This should be ported to Python

$/ = undef;

%options = ();
while ($ARGV[0] =~ /^-/) {
    $option = shift @ARGV;
    $value = shift @ARGV;
    $options{$option} = $value;
}

# use default text body tag or one supplied by user
$TextBodyTag = "TEXT";
if ($options{'-t'}) {
    $TextBodyTag = $options{'-t'};
}

$inputfile = shift;
$outputfile = shift;
$tmpfile = $inputfile . '.tmp';

$TextBodyStartTag = "<${TextBodyTag}[^>]*>";  # made more general (MV 070301)
$TextBodyEndTag = "<\/$TextBodyTag>";

open (IN, "$inputfile") or die "Cannot open $inputfile\n";
$text = <IN>;
close IN;
    
# Isolate wrapping tag and the body
if ( $text =~ /($TextBodyStartTag)(.+?)($TextBodyEndTag)/s) {
    $opentag = $1;
    $closetag = $3;
    $body = $2;
}

# Prepare input for TimeTag and save to tmp file, include the DCT
$DateTime = &getDCT();
$body = CleanUp($body);
$GUTimeTagSource = "<DOC>\n" . $DateTime . "\n" . $body . "</DOC>\n";
&saveToFile($GUTimeTagSource, $tmpfile);

# GUTime Tagging
$output = `perl TimeTag.pl $tmpfile | perl postTempEx.pl`;
$output =~ s/<DATE_TIME>.*?<\/DATE_TIME>\n//;
$output =~ s/<DOC>\n//;
$output =~ s/<\/DOC>\n//;
$output =~ s/^\n//;
&saveToFile($opentag.$output.$closetag, $outputfile);


sub CleanUp
{
    # Cleans up a source string to run GUTime, removes chunking tags,
    # Evita tags, and RTE3 tags. Should be more general.
    
    my $line = $_[0];

    @rte_tags = qw ( h t );
    @chunk_tags = qw( NG NX HEAD
                      VG VX NGP POS VG-INF VG-VBG VG-VGB VG-VBN VNX INF VGX
                      RX RG AX-PRENOMINAL IN-MW );

    foreach $tag (@chunk_tags, @rte_tags) {
        $line =~ s/<$tag>//ig;
        $line =~ s/<\/$tag>//ig;
    }

    # remove evita tags
    $line =~ s/<EVENT[^>]+?>//ig;
    $line =~ s/<\/EVENT>//ig;
    $line =~ s/<MAKEINSTANCE[^>]+?\/>//ig;

    @atee_tags = qw (HandL Title Headline Para LeadPara TailParas
                     Byline Credit Contact Notes Copyright Art ELink);
    foreach $tag (@atee_tags) {
        $line =~ s/<$tag[^>]*>//ig;
        $line =~ s/<\/$tag>//ig;
    }
    
    return $line;
}


sub saveToFile
{
    my ($text, $filename) = @_;
    open (OUT, "> $filename") or die "Could not save to $filename\n";
    print OUT $text;
    close OUT;
}


sub getDCT
{
    if ($options{'-dct'}) {
        $DateTime = '<DATE_TIME>' . $options{'-dct'} . '</DATE_TIME>';
    } else {
        #print STDERR "Warning: no document date found, using current date\n";
        my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst)=localtime(time);
        $year = $year + 1900;
        $year =~ /\d\d(\d\d)/;
        $year = $1;
        $DateTime = sprintf "<DATE_TIME>%02d/%02d/%02d</DATE_TIME>", $year,$mon+1,$mday;
    }
    return $DateTime;
}


