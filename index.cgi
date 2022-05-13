#!/usr/bin/perl
#
# http://192.168.1.13/cgi-bin/jnsa/
#
#
use strict;
use warnings;
use CGI;

use lib "./";
use dp;

my $DEBUG = 0;
my $jnsa_hist = "./jnsa-nenpyou.tsv";
my $htmlf     = "./jnsa-nenpyou.html";
my $dlm = "\t";
my $NA = "N/A";


my $HTML_STYLE = <<_EOSTYLE_;
.upload {
	display: none;
	color: #f0f0f0; /* ラベルテキストの色を指定する */
	background-color: #000000;/* ラベルの背景色を指定する */
	padding: 10px; /* ラベルとテキスト間の余白を指定する */
	border: double 4px #f0f0f0;/* ラベルのボーダーを指定する */
}

table.form {
  border: 1px solid gray;
}
table.form th, .table1 td {
  border: 1px solid gray;
}

/* 奇数行のスタイル */
table.sample tr:nth-child(odd){
  background-color:aliceblue;
}
 
/* 偶数行のスタイル */
table.sample tr:nth-child(even){
  background-color:white;
}
_EOSTYLE_

my $MY_URL = $ENV{REQUEST_URI};

# Group   Year    Month   Day     Time    End Year        End Month       End Day End Time        Display Date    Title   Detail  林コメント/修正案       URL     Image URL       Im age Credit      Type    Color

my $form_params = [
	[
		{tag => "Group", method => "select", 
			params => ["世の中:society", "IT:IT", "政府機関:gov", "セキュリティ:security",
					 "JNSA:jnsa", "JNSA活動:JNSA-act", "JNSA会員数:JNSA-member", ]
		},
		{tag => "Year", method => "select",
			params => [2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011],
		},
		{tag => "Search", method => "text",
			display_str => "seach", params => {size => 20, },
		},
    	# push(@forms, '<p><input type="submit" name="submit" value="送信" /></p>' . "\n");
		{tag => "Download", method => "submit", display_str => "Download",}, 
		{tag => "upload", method => "file", display_str => "upload data", params => {accept => "text/csv,image/plain"}}, 
		{tag => "送信", method => "submit", display_str => "送信", },
	],

];

my $param_index = {};
my $param_vals = {};
foreach my $params (@$form_params){
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
}

my 	$DISPLAY_ITEMS = ["Display Date", "Group", "Title", "Detail"];
my 	$DISPLAY_ITEMS_NO = [];

#
#	CGI Params
#
my $PARAMS = {};
my $q = new CGI;

my @names = $q->param;
my $cgi = 1;
if($MY_URL){		# command line
	foreach my $nm (@names){
		my @w = $q->param($nm);
		my $p = $param_index->{$nm};
		if($p->{method} eq "select"){
			$PARAMS->{$nm} = [$q->param($nm)] if(! (grep{$_ eq $NA} @w));
		}
		else { 
			$PARAMS->{$nm} = [$q->param($nm)]; 
		}
	}
}
else {
	$MY_URL = "command_line";
	$cgi = 0;
	@names = ();
	my @dm_params = ["Group:society", "Year:2001", "Search:", "submit:送信"];
	foreach my $p (@dm_params){
		my($nm, @vals) = split(/:/, $p);
		push(@names, $nm);
		$PARAMS->{$nm} = [@vals];
	}
}

#
#	Gen HTML
print &html_header("JNSA 年表") . "\n";
print "<body>\n";

if(1){		# Dump parameters
	print "<br>";
	foreach my $nm (@names){
		my @vals = ($cgi) ? $q->param($nm) : @{$PARAMS->{$nm}};
		print "[" . join(":", $nm, @vals) . "]\n";
	}
	#dp::dp "[$0]\n";
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
#dp::dp "### [$skey] ###\n" if($DEBUG);
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
			#dp::dp "[$key:$v:" . join(@$kv) . "]" if($rn < 5);
			my $hit = 0;
			foreach my $pv (@$kv){
				my $dsp = $param_vals->{$key}->{$pv};
				$hit++ if($v eq $param_vals->{$key}->{$pv});

				#dp::dp "($hit :$v:$pv:" . join(",", keys %{$param_vals->{$key}}, "<$dsp>") . ")" if($rn < 5);
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
foreach my $params (@$form_params){
	print '<table class="form" border="1">' . "\n";
	&print_form($params);			# forms
	print '</table>' . "\n";
}
print "<hr>\n";


print '<table class="sample">' . "\n";
$head =  &gen_tag("<tr>", &print_item("<th>", @$DISPLAY_ITEMS)); 
print $head . "\n";
my $last_date = "0000-00";
my @item_list = ();

my $na = {};
foreach my $k (@ITEM_LIST){
	#dp::dp "$k\n";
	#$na->{$k} = "&nbsp;";
	$na->{$k} = "-";
}

foreach my $item (sort {$a->{"Display Date"} cmp $b->{"Display Date"}} @NENPYOU){
	$item->{"Display Date"} =~ /\d{4}-\d{2}/;
	my $item_date = $&;
	if($item_date eq $last_date){
		push(@item_list, $item);
		next;
	}

	#dp::dp "[$last_date:$item_date]" . join(",", &item_list($item, $DISPLAY_ITEMS_NO)) . "\n";

#	my $html =  &gen_tag("<tr>", &print_item("<td>", &item_list($item, $DISPLAY_ITEMS_NO))) ; 
	my $html =  &gen_tag("<tr>", &print_item_list("<td>", @item_list)) ; 
	print $html . "\n";

	foreach my $ym (&month_diff($last_date, $item_date)){
		#dp::dp ">>>> $ym" . "\n";
		$na->{"Display Date"} = $ym . "-00";
		my $html = &gen_tag("<tr>", &print_item("<td>", &item_list($na, $DISPLAY_ITEMS_NO))) ; 
		print $html . "\n";
	}

	@item_list = ($item);
	$last_date = $item_date;
}
if($#item_list >= 0){
	my $html =  &gen_tag("<tr>", &print_item_list("<td>", @item_list)) ; 
	print $html . "\n";
}

print "</table>\n";
print "</body>\n";
print "</html>\n";

exit 0;


sub	month_diff
{
	my ($last_date, $item_date) = @_;
	if($last_date lt "2000-00"){
		return ();
	}

	#dp::dp "[$last_date:$item_date]\n";
	my @month = ();
	$last_date =~ /(\d{4})-(\d{2})/;
	my ($y, $m) = ($1, $2);
	for(;;){
		($y, $m) = &increment_month($y, $m);
		my $date = sprintf("%04d-%02d", $y, $m);
		last if($date ge $item_date);

		#dp::dp "[$date:$item_date]\n";
		push(@month, $date);
	}
	return (@month);
}

sub	increment_month
{
	my($y, $m) = @_;

	if($m < 12){
		$m++;
	}
	else {
		$m = 0;
		$y++;
	}
	return ($y, $m);
}

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
sub	print_item_list
{
	my ($tag, @items) = @_;
	$tag = $tag//$dlm;

	my @item_list = ();	
	foreach my $item (@items){
		my @w = &item_list($item, $DISPLAY_ITEMS_NO); 
		#dp::dp join(",", @w) . "\n";
		push(@item_list, [@w]) ; 
	}

	my $str = "";
	foreach (my $i = 0; $i < scalar(@$DISPLAY_ITEMS_NO); $i++){
		my @w = ();
		foreach my $item (@item_list){
			push(@w, $item->[$i]);
		}
		my $s = join("<br>", @w);
		my $it = &gen_tag($tag, $s);
		#dp::dp "[$it]\n";
		$str .= $it;
	}
	return $str;
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
	my ($params) = @_;

	print '<form action="' . $MY_URL . '" method="post">'. "\n";
	my @w = ();
	foreach my $p (@$params){
		my $head = $p->{display_str}//"";
		$head = $p->{tag} if(! $head); 
		push(@w, $head);
		#dp::dp "[$params]" . $p->{tag} . "\n";
	}
	#my $submit = $params->[scalar(@$params) - 1];
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
		elsif($p->{method} eq "text"){
			$str .= '<label for"' . $p->{tag} . '"' . $p->{display_str} . '</label>' . "\n";
			$str .= "\t" . '<input type="text" id="' . $p->{tag} . '" name="' . $p->{tag} 
					. '" ';
			#dp::dp "[$tag] [$PARAMS->{$tag}] " . ($PARAMS->{$tag}->[0]//"") . "\n";
			$str .= (defined $PARAMS->{$tag}) ? 'value="'.($PARAMS->{$tag}->[0]//"").'" ' : "";
			$str .= &add_params($p);
			$str .=  '/>' . "\n";

		}
		elsif($p->{method} eq "file"){
			#$str = sprintf('<p><label> Select <input type="%s" class="upload" /></label></p>', 
			#			$p->{method}, $p->{tag}, &add_params($p)) . "\n";
			$str = sprintf('<p><input type="%s" name="%s" %s></p>', 
						$p->{method}, $p->{display_str}, &add_params($p)//"") . "\n";
		}
		elsif($p->{method} eq "submit"){
			$str = sprintf('<p><input type="%s" name="%s" value="%s"></p>',
						 $p->{method}, $p->{tag}, $p->{display_str}) . "\n";
		}
		#print $str ;
		#print "-" x 20 . "\n";
		push(@forms, $str . "\n");
	}
	#print '</p>' . "\n";
	#my $submit_str = sprintf('<p><input type="%s" name="%s" value="%s" /></p>', $submit->{method}, $submit->{tag}, $submit->{display_str}) . "\n";
	#push(@forms, $submit_str);
    #push(@forms, '<p><input type="submit" name="submit" value="送信" /></p>' . "\n");

	print &gen_tag("<tr>", &print_item('<td valign="top">', @forms)) . "\n"; 
	print '</form>' . "\n";
}

sub	add_params
{
	my ($p) = @_;

	my $str = "";
	foreach my $t (keys %{$p->{params}}){
		my $v = $p->{params}->{$t}//"";
		if($v){
			$str .= $t . '="' . $v . '" ';
		}
		else {
			$str .= $t . ' ';
		}
	}
	return $str;
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
$HTML_STYLE
</style>
</head>
_EOHTML_

	$HTML_HEAD =~ s/#TITLE#/$title/g;
	return $HTML_HEAD;

}


