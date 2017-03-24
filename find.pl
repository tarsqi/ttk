#!/usr/bin/perl

$pattern = shift;
$fancy = shift;

@commands = ("grep -n -e '$pattern' *.py",
             "grep -n -e '$pattern' */*.py",
             "grep -n -e '$pattern' */*/*.py",
             "grep -n -e '$pattern' */*/*/*.py");

foreach $command (@commands) {
    print "\n>>> $command\n\n";
    $results = `$command`;
    if($fancy) {
        foreach $result (split("\n", $results)) {
            $result =~ /(.*:\d+):\s*(.*)/;
            printf "%-30s %s\n", ($1, $2);
        }
        print "\n";
    } else {
        print "$results\n";
    }
}
