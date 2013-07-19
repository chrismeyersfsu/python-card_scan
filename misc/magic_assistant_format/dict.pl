#!/usr/bin/perl

# Convert abbreviation to full csv to python dictionary
# usage: cat abbrev_to_full.csv | ./dict.pl

while (my $line = <STDIN>) {
	chomp($line);
	
	my ($abbrev, $full) = split(/,/, $line);
	print "'$abbrev': '$full',\n";
}
