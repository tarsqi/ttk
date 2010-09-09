#!/bin/perl

$dir1 = shift;
$dir2 = shift;

opendir DIR, $dir1 or die;

foreach $file (readdir DIR) 
{
	#print "$file\n";
	next unless $file =~ /xml/;
	$command = "diff $dir1/$file $dir2/$file";
	#print "$command\n";
	$result = `$command`;
	if ($result) {
		print "$file has changed\n";
	}
}

