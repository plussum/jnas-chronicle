#!/usr/bin/perl
#
#
#	https://docs.google.com/spreadsheets/d/1RGa0W19wC2NXOm4Fd_6eYlw_NPgbud2EbuU8aobZh2s/edit#gid=1801759358
#
use strict;
use warnings;
use utf8;

my $DEBUG = 0;

#binmode(STDOUT, ":utf8");

my $key = '1RGa0W19wC2NXOm4Fd_6eYlw_NPgbud2EbuU8aobZh2s';
my $gid = '1801759358';
my $format = 'tsv';
my $fname = "jnsa-nenpyou" . ".$format";

my $url = "https://docs.google.com/spreadsheets/d/$key/export?gid=$gid&format=$format";
my $cmd = "wget -O $fname '$url'";

print  "-" x 40 . "\n";
print $cmd . "\n";
system($cmd);

if($DEBUG){
	print  "-" x 40 . "\n";

	open(FD, $fname) || die "$fname";
	my $ln = 0;
	while(<FD>){
		last if($ln++ > 20);
		print $_;
	}
	close(FD);
}
exit 0;
