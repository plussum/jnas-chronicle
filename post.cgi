#!/usr/bin/perl
#
#
#
use strict;
use warnings;

use CGI;

my $DEBUG = 0;
my $jnsa_hist = "./jnsa-nenpyou.tsv";
my $htmlf     = "./jnsa-nenpyou.html";
my $dlm = "\t";
my $NA = "N/A";

my $MY_URL = $ENV{REQUEST_URI};

my $params = [
	{tag => "Group", method => "select", 
		params => ["世の中:society", "IT:IT", "政府機関:gov", "セキュリティ:security",
				 "JNSA:jnsa", "JNSA活動:JNSA-act", "JNSA会員数:JNSA-member", ]
	},
	{tag => "Date", method => "select",
		params => [2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 
					2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 
					2020, 2021, 2022, 2023,
				],
	},
	{tag => "Title", method => "text",
		display_str => "Title", params => {size => 60 },
	},
	{tag => "Detail", method => "textarea",
		display_str => "detail", params => {rows => 4, cols => 60, },
	},
];

my $param_index = {};
my $param_vals = {};
foreach my $p (@$params){
	my $tag = $p->{tag};
	$param_index->{$tag} = $p;
	$param_vals->{$tag} = {};
	if($p->{method} eq "select"){
		foreach my $pp (@{$p->{params}}){
			my ($dsp, $v) = split(/:/, $pp);
			$v = $v//$dsp;
			$param_vals->{$tag}->{$v} = $dsp;
		}
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
	my $p = $param_index->{$nm};
	if($p->{method} eq "select"){
		$PARAMS->{$nm} = [$q->param($nm)] if(! (grep{$_ eq $NA} @w));
	}
	else { 
		$PARAMS->{$nm} = [$q->param($nm)]; 
	}
#	print join(":", $nm, @vals) . "<br>\n";
}

#
#	Gen HTML
print &html_header("JNSA 年表") . "\n";
print "<body>\n";

if($DEBUG){		# Dump parameters
	print "<br>";
	foreach my $nm (@names){
		my @vals = $q->param($nm);
		print "[" . join(":", $nm, @vals) . "]\n";
	}
	print "<br>";
}

#
#
#	Load Data
#
my @NENPYOU = ();
open(FD, $jnsa_hist) || die "cannot open $jnsa_hist";
my $head = <FD>;
chop($head);
my @ITEM_LIST = split(/$dlm/, $head);

my $skey = $PARAMS->{Search}->[0]//"";
print "### [$skey] ###\n" if($DEBUG);
my $rn = 0;
while(<FD>){
	s/[\r\n]+$//;
	my @w = split(/$dlm/, $_);
	next if(! $w[0]//"");

	if($skey){					# Search 
		next if(! /$skey/);	
	}
	my $item = {};
	$item->{rn} = $rn++;
	my $disp_flag = 1;
	for(my $i = 0; $i <= $#w; $i++){
		my $key = $ITEM_LIST[$i]//"-NONE $i-";
		my $v = $w[$i];
		$item->{$key} = $v;
		if(defined $PARAMS->{$key}){		# Check Selected parameter for Group, Year
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
	next if(! $disp_flag);			# data does not much the parameter

	my $dd = $item->{"Display Date"}//"";	# Set Display date from Year, Month, Day  
	if(! $dd ||  !($dd =~ /-\d{4}/)){
		my $ymd = sprintf("%04d-%02d-%02d", 
			&numeric($item->{Year}), &numeric($item->{Month}), &numeric($item->{Day}));
		$item->{"Display Date"} = $ymd;
	}
	push(@NENPYOU, $item);			# Records to display
}
close(FD);

#
#	Set array no of Display_ITEMS
#
foreach my $item (@$DISPLAY_ITEMS){
	for(my $i = 0; $i <= $#ITEM_LIST; $i++){
		if($item eq $ITEM_LIST[$i]){
			push(@$DISPLAY_ITEMS_NO, $i);
			last;
		}
	}
}


#
#	Print HTML
#
&print_form();			# forms
print "<hr>\n";

print '<table class="sample">' . "\n";
$head =  &gen_tag("<tr>", &print_item("<th>", @$DISPLAY_ITEMS)); 
print $head . "\n";
foreach my $item (sort {$a->{"Display Date"} cmp $b->{"Display Date"}} @NENPYOU){
	my $html =  &gen_tag("<tr>", &print_item("<td>", &item_list($item, $DISPLAY_ITEMS_NO))) ; 
	print $html . "\n";
}
print "</table>\n";
print "</body>\n";
print "</html>\n";

exit 0;

#
#
#
sub	numeric
{
	my ($n) = @_;
	$n = $n//"";

	$n =~ s/\s//g;
	$n = 0 if(!$n);
   	$n = 0 if($n =~ /\D/);
	return $n;
}
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
	$etag =~ s/ .*>/>/;
	return ($tag . " $str " . $etag . "\n");
}

sub	print_form
{

	print '<form action="' . $MY_URL . '" method="post">'. "\n";
	print '<table>' . "\n";
	my @w = ();
	foreach my $p (@$params){
		push(@w, $p->{tag});
	}
	print &gen_tag("<tr>", &print_item("<th>", @w)) . "\n"; 

	my @forms = ();
	foreach my $p (@$params){
		my $tag = $p->{tag};
		my $str = "";
		if($p->{method} eq "select"){
			my @group = @{$p->{params}};
			$str .= '<select name="' . $p->{tag} . '" size="' . "5" . '" multiple="multiple">' . "\n";

			my @selected_list = (defined $PARAMS->{$tag}) ? @{$PARAMS->{$tag}} : ();
			foreach my $g ("$NA:$NA", @group, "$NA:$NA"){
				my ($dsp, $val) = split(/:/, $g);
				$val = $val//$dsp;
				my $select = (grep{$_ eq $val} @selected_list) ? 'selected="selected"' : "";
				$str .= "\t" . '<option ' . $select . 'value="' . $val . '">' . $dsp . '</option>' . "\n";
			}
			$str .= '</select>' . "\n";
		}
		elsif($p->{method} eq "textarea"){		# TEXTAREA
			$str .= '<label for"' . $p->{tag} . '"' . $p->{display_str} . '</label>' . "\n";
			$str .= "\t" . '<textarea name="' . $p->{tag} . '" ';
			$str .= (defined $PARAMS->{$tag}) ? 'value="'.$PARAMS->{$tag}->[0].'" ' : "";
			foreach my $t (keys %{$p->{params}}){
				my $v = $p->{params}->{$t}//"";
				if($v){
					$str .= $t . '="' . $v . '" ';
				}
				else {
					$str .= $t . ' ';
				}
			}
			$str .= '>';
			$str .= (defined $PARAMS->{$tag}) ? $PARAMS->{$tag}->[0] : "";
			$str .= "</textarea>\n";
		}
		elsif($p->{method} eq "text"){			# TEXT
			$str .= '<label for"' . $p->{tag} . '"' . $p->{display_str} . '</label>' . "\n";
			$str .= "\t" . '<input type="text" id="' . $p->{tag} . '" name="' . $p->{tag} . '" ';
			$str .= (defined $PARAMS->{$tag}) ? 'value="'.$PARAMS->{$tag}->[0].'" ' : "";
			foreach my $t (keys %{$p->{params}}){
				my $v = $p->{params}->{$t}//"";
				if($v){
					$str .= $t . '="' . $v . '" ';
				}
				else {
					$str .= $t . ' ';
				}
			}
			$str .=  '>' . "\n";
		}

		#print $str ;
		#print "-" x 20 . "\n";
		push(@forms, $str . "\n");
	}
	#print '</p>' . "\n";
    push(@forms, '<p><input type="submit" name="submit" value="送信" /></p>' . "\n");

	print &gen_tag("<tr>", &print_item('<td valign="top">', @forms)) . "\n"; 
	print '</table>' . "\n";

	print '</form>' . "\n";
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
/*
.table1 {
  border: 1px solid gray;
}
.table1 th, .table1 td {
  border: 1px solid gray;
}
*/
/* 奇数行のスタイル */
table.sample tr:nth-child(odd){
  background-color:aliceblue;
}
 
/* 偶数行のスタイル */
table.sample tr:nth-child(even){
  background-color:white;
}
</style>
</head>
_EOHTML_

	$HTML_HEAD =~ s/#TITLE#/$title/g;
	return $HTML_HEAD;

}


