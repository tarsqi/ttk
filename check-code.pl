# check-code.pl
# -------------

# Recursively checks python code files in <dir>. The only check
# currently is for tabs.
#
# USAGE: perl check-code.pl <dir>




my $dir = shift;
my @files_with_tabs = ();

&check_dir($dir, 0);

print "\nFILES WITH TABS:\n";
foreach my $f (@files_with_tabs) {
    print "  $f\n";
}
print "\n";

sub check_dir
{
    my $dir = shift;
    my $indent = shift;
    
    print ' ' x $indent, "$dir\n";
    opendir DIR, $dir or die "Error: could not open directory '$dir'\n\n";
    my @files = readdir DIR;
    #print ' ' x $indent, "  @files\n";
    foreach my $file (@files) {
        #print ' ' x ($indent+3), "$dir/$file\n";
        next if $file eq '.';
        next if $file eq '..';
        if (-d "$dir/$file") {
            &check_dir("$dir/$file", $indent+3);
        } elsif ($file =~ /\.py$/) {
            &check_file("$dir/$file", $indent+3);
        }
    }
}

sub check_file
{
    my $file = shift;
    my $indent = shift;
    print ' ' x $indent, "$file\n";
    open IN, $file or die;
    $line = 0;
    while (<IN>) {
        $line++;
        if (/\t/) {
            print ' ' x $indent, " WARNING: contains tabs\n";
            push @files_with_tabs, "$file (line $line)";
            return
        }
    }
}
