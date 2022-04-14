#!/usr/bin/perl
#
#
#
use strict;
use warnings;

use CGI;

my $jnsa_hist = "./jnsa-nenpyou.tsv";
my $htmlf     = "./jnsa-nenpyou.html";
my $dlm = "\t";
my $NA = "N/A";

my $MY_URL = $ENV{REQUEST_URI};

# Group   Year    Month   Day     Time    End Year        End Month       End Day End Time        Display Date    Title   Detail  林コメント/修正案       URL     Image URL       Im age Credit      Type    Color

my $params = [
	{tag => "Group", method => "select", 
		params => ["世の中:society", "IT:IT", "政府機関:gov", "セキュリティ:security", "JNSA:jnsa"]
	},
	{tag => "Year", method => "select",
		params => [2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011],
	},
];

my $param_vals = {};
foreach my $p (@$params){
	my $tag = $p->{tag};
	$param_vals->{$tag} = {};
	foreach my $pp (@{$p->{params}}){
		my ($dsp, $v) = split(/:/, $pp);
		$v = $v//$dsp;
		$param_vals->{$tag}->{$v} = $dsp;
	}
}


my 	$DISPLAY_ITEMS = ["Group", "Display Date", "Title", "Detail"];
my 	$DISPLAY_ITEMS_NO = [];

#
#	CGI Params
#
my $PARAMS = {};
my $q = new CGI;
my @names = $q->param;

foreach my $nm (@names){
	my @w = $q->param($nm);
	$PARAMS->{$nm} = [$q->param($nm)] if(! (grep{$_ eq $NA} @w));
#	print join(":", $nm, @vals) . "<br>\n";
}

#
#	Gen HTML
print &html_header("JNSA 年表") . "\n";
print "<body>\n";
#print join("\t", @ITEM_LIST) . "\n";

#
#
#	Load Data
#
my @NENPYOU = ();
open(FD, $jnsa_hist) || die "cannot open $jnsa_hist";
my $head = <FD>;
chop($head);
my @ITEM_LIST = split(/$dlm/, $head);

my $rn = 0;
while(<FD>){
	s/[\r\n]+$//;
	my @w = split(/$dlm/, $_);
	next if(! $w[0]//"");

	my $item = {};
	$item->{rn} = $rn++;
	my $disp_flag = 1;
	for(my $i = 0; $i <= $#w; $i++){
		my $key = $ITEM_LIST[$i]//"-NONE $i-";
		my $v = $w[$i];
		$item->{$key} = $v;
		if(defined $PARAMS->{$key}){
			my $kv = $PARAMS->{$key};
			#print "[$key:$v:" . join(@$kv) . "]" if($rn < 5);
			my $hit = 0;
			foreach my $pv (@$kv){
				my $dsp = $param_vals->{$key}->{$pv};
				$hit++ if($v eq $param_vals->{$key}->{$pv});

				#print "($hit :$v:$pv:" . join(",", keys %{$param_vals->{$key}}, "<$dsp>") . ")" if($rn < 5);
			}
			if($hit <= 0){
				$disp_flag = 0;
				last;
			}
		}
	}
	next if(! $disp_flag);

	my $dd = $item->{"Display Date"}//"";
	if(! $dd ||  !($dd =~ /-\d{4}/)){
		my $ymd = sprintf("%04d-%02d-%02d", $item->{Year}//"", $item->{Month}//"", $item->{Day}//"");
		$item->{"Display Date"} = $ymd;
	}

	push(@NENPYOU, $item);
}
close(FD);


foreach my $item (@$DISPLAY_ITEMS){
	for(my $i = 0; $i <= $#ITEM_LIST; $i++){
		if($item eq $ITEM_LIST[$i]){
			push(@$DISPLAY_ITEMS_NO, $i);
			last;
		}
	}
}



#
#
#
print "<br>";
foreach my $nm (@names){
	my @vals = $q->param($nm);
	print "[" . join(":", $nm, @vals) . "]\n";
}
print "<br>";

&print_form();
print "<hr>\n";

#
#
#
print "<table>\n";
$head =  &gen_tag("<tr>", &print_item("<th>", @$DISPLAY_ITEMS)); 
print $head . "\n";
foreach my $item (@NENPYOU){
	my $html =  &gen_tag("<tr>", &print_item("<td>", &item_list($item, $DISPLAY_ITEMS_NO))); 
	print $html . "\n";
}
print "</table>\n";
print "</body>\n";
print "</html>\n";


sub	print_item
{
	my ($tag, @items) = @_;
	$tag = $tag//$dlm;

	my $str = "";
	foreach my $v (@items){
		my $it = &gen_tag($tag, $v);
		#print "[$it]\n";
		$str .= $it;
	}
	return $str;
}

sub	item_list
{
	my ($item, $targets) = @_;

	my @vals = ();
	for(my $i = 0; $i < $#ITEM_LIST; $i++){
		my $key = $ITEM_LIST[$i]//"-NONE $i-";
		push(@vals, $item->{$key}//"");
	}
	my @ww = ();
	foreach my $i (@$targets){
		push(@ww, $vals[$i]);
	}
	return @ww;
}

sub	gen_tag
{
	my($tag, $str) = @_;

	my $etag = $tag;
	$etag =~ s/\</\<\//;
	return ($tag . " $str " . $etag);
}


sub	html_header
{
	my ($title) = @_;
	$title = $title//"--";

my $HTML_HEAD = <<_EOHTML_;
Content-type: text/html

 
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title> #TITLE# </title>
<style>
.table1 {
  border: 1px solid gray;
}
.table1 th, .table1 td {
  border: 1px solid gray;
}
</style>
</head>
_EOHTML_

	$HTML_HEAD =~ s/#TITLE#/$title/g;
	return $HTML_HEAD;

}


sub	print_form
{

	print '<form action="' . $MY_URL . '" method="post">'. "\n";
	foreach my $p (@$params){
		my @group = @{$p->{params}};
		my $tag = $p->{tag};
		print $tag. ":\n";
		#print '<select name="Group" size="' . ($#group+1) . '" multiple="multiple">' . "\n";
		print '<select name="' . $p->{tag} . '" size="' . "5" . '" multiple="multiple">' . "\n";

		my @selected_list = (defined $PARAMS->{$tag}) ? @{$PARAMS->{$tag}} : ();
		foreach my $g ("$NA:$NA", @group, "$NA:$NA"){
			my ($dsp, $val) = split(/:/, $g);
			$val = $val//$dsp;
			my $select = (grep{$_ eq $val} @selected_list) ? 'selected="selected"' : "";
			print '<option ' . $select . 'value="' . $val . '">' . $dsp . '</option>' . "\n";
		}
		print '</select>' . "\n";
	}
	#print '</p>' . "\n";
    print '<p><input type="submit" name="submit" value="送信" /></p>' . "\n";
	print '</form>' . "\n";
}


