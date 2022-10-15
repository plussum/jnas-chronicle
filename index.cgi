#!/usr/bin/perl
#
# http://192.168.1.13/cgi-bin/jnsa/
#
#
use strict;
use warnings;
use CGI;
use File::Copy;

use lib "./";
use dp;

my $DEBUG = 0;
my $jnsa_hist = "./jnsa-nenpyou.tsv";
my $htmlf     = "./jnsa-nenpyou.html";
my $spread_sheet = 'https://docs.google.com/spreadsheets/d/1RGa0W19wC2NXOm4Fd_6eYlw_NPgbud2EbuU8aobZh2s/edit?pli=1#gid=1801759358';
my $MY_URL = $ENV{REQUEST_URI};
my $dlm = "\t";
my $NA = "ALL";
my $NIL = "NIL";
my $EMPTY_MONTH = 1;

my @table_color = ("white", "lightsteelblue"); #"aliceblue");
my $DISPLAY_DEFS = [ {item => "rn", width => 10, align => "right"},
					{item => "Evaluation", width => 20, align => "center"},
					{item => "Display Date", witdh => 150,},
					{item => "Group", width => 200, },
					{item => "Title", width => 600, },
					{item => "InCharge", width => 60, align => "center"},
					{item => "Checker", width => 60,align => "center"},
				];
my $DISPLAY_ITEMS_NO = [];
my @dm_params = ("Group:", "Year:2000", "Search:", "送信:送信", ); #"Download:Download");


# Group   Year    Month   Day     Time    End Year        End Month       End Day End Time        Display Date    Evaluation
#		Title   Detail  林コメント/修正案       URL     Image URL       Im age Credit      Type    Color
#
#	Form Parameters
#

# cat jnsa*.tsv | cut  -f 14 | sort | uniq
my	@members = ("伊藤", "永野", "河本", "丸山", "高橋", "持田", "小屋",
						"西尾", "中山", "唐沢", "畑",   "冨田",);
my $form_params = [
	[
		{tag => "Evaluation", method => "select", 
			params => [0,1, $NIL]
		},
		{tag => "Group", method => "select", 
			params => ["世の中:society", "IT:IT", "政府機関:gov", "セキュリティ:security",
					 "JNSA:jnsa", "JNSA活動:JNSA-act", "JNSA会員数:JNSA-member", ]
		},
		{tag => "Year", method => "select",
			params => [ 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011,
						2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022],
		},
		{tag => "Search", method => "text",
			display_str => "seach", params => {size => 20, },
		},
		{tag => "InCharge", method => "select",
			params => [@members],
		},
		{tag => "Checker", method => "select",
			params => [@members],
		},
		{tag => "Debug", method => "select", 
			params => [0,1]
		},

		{tag => "Download", method => "submit", display_str => "Download",}, 
		{tag => "送信", method => "submit", display_str => "送信", },
	],
];

#	Compile Form Parameters
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

#
#	Get CGI Parameters
#
my $q = new CGI;
my @names = $q->param;
my $PARAMS = {};
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
else {		# for commandline debug
	$MY_URL = "command_line";
	$cgi = 0;
	@names = ();
	foreach my $p (@dm_params){
		my($nm, @vals) = split(/:/, $p);
		dp::dp "$nm: $#vals\n";
		if($#vals >= 0){
			push(@names, $nm);
			$PARAMS->{$nm} = [@vals] ;
		}
	}
}
if($PARAMS->{Debug}//""){
	$DEBUG = 1;
}
if(($PARAMS->{Checker}//"") || ($PARAMS->{InCharge}//"")){
	$EMPTY_MONTH = 0;
}

#
#	Gen HTML, output befor loading data for debug print
#
print &html_header("JNSA 年表") . "\n";
print "<body>\n";

#	Set CGI parameters to the array
my $params = {};
foreach my $nm (@names){
	my @vals = ($cgi) ? $q->param($nm) : @{$PARAMS->{$nm}};
	$params->{$nm} = [@vals];
}
if($DEBUG){		# Dump parameters
	print "<br>";
	foreach my $nm (keys %$params){
		print "[" . join(":", $nm, @{$params->{$nm}}) . "]\n";
	}
	#dp::dp "[$0]\n";
	print "<br>";
}

#
#	Download Chronicle data from Google Drive
#
my @dl = ();
@dl = @{$params->{Download}} if(defined $params->{Download});
#print "Download: " . join(",", $#dl, @dl) . "<br>\n";
if($#dl >= 0 ){
	print "Download<br>\n";
	&downlad_chroncile();
}

#
#	Load Chronicle Data
#
my @NENPYOU = ();
open(FD, $jnsa_hist) || die "cannot open $jnsa_hist";
my $head = <FD>;
chop($head);
my @ITEM_LIST = split(/$dlm/, $head);

my $skey = $PARAMS->{Search}->[0]//"";		# Serach parameter in CGI
#dp::dp "### [$skey] ###\n" if($DEBUG);
my $rn = 0;
while(<FD>){
	s/[\r\n]+$//;
	#dp::dp $_ . "\n";

	my $str = &escape_html($_);				# for injection
	my @w = split(/$dlm/, $str);
	next if(! $w[0]//"");					# No data in first col (Group), go Next
	next if($skey && (! /$skey/));			# No Skey in the data, go Next

	my $item = {};
	$item->{rn} = $rn++;
	my $disp_flag = 1;
	for(my $i = 0; $i <= $#ITEM_LIST; $i++){		# col data
		my $key = $ITEM_LIST[$i]//"-NONE $i-";	# for debug, set NONE when the data is ""
		my $v = $w[$i]//"";
		$item->{$key} = $v;					# set value of  key 
		#dp::dp "[$key][$v]<br>\n" if($key eq "URL");
		#dp::dp "[$i:$key:$v]<br>\n";
		if(defined $PARAMS->{$key}){		# Check Selected parameter for Group, Year
			my $kv = $PARAMS->{$key};
			#dp::dp "[$key:$v:" . join(@$kv) . "]\n" if($rn < 5);
			my $hit = 0;
			foreach my $pv (@$kv){
				my $dsp = $param_vals->{$key}->{$pv}//"#None#";
				if($dsp eq $NIL){			# for NIL (No data)
					$dsp = "";
				}
				#$hit++ if($v eq $dsp);
				$hit++ if($v =~ /$dsp/);
				#dp::dp "($hit :$v:$pv:" . join(",", keys %{$param_vals->{$key}}, "<$dsp>") . ")<br>" ;#if($rn < 5);
			}
			if($hit <= 0){					# no target data if one selected item does not hit
				$disp_flag = 0;
				last;
			}
		}

	}
	next if($disp_flag <= 0);					# data does not much the parameter

	#dp::dp "[HIT] $_ <br>\n";
	my $dd = $item->{"Display Date"}//"";	# Set Display date from Year, Month, Day  
	if(! $dd ||  !($dd =~ /-\d{4}/)){
		my $ymd = sprintf("%04d-%02d-%02d", 
			&numeric($item->{Year}), &numeric($item->{Month}), &numeric($item->{Day}));
		$item->{"Display Date"} = $ymd;
	}
	#dp::dp join(",", $item->{Title}, $item->{URL}) . "<br>\n";
	push(@NENPYOU, $item);					# Records to display
}
close(FD);

#
#	Set array # of Display_ITEMS
#
foreach my $def (@$DISPLAY_DEFS){
	my $cl = 0;
	for(; $cl <= $#ITEM_LIST; $cl++){
		if($def->{item} eq $ITEM_LIST[$cl]){
			last;
		}
	}
	$cl = $def->{item} if($cl > $#ITEM_LIST);
	push(@$DISPLAY_ITEMS_NO, $cl);
}

########################################
#
#	Output HTML data
#
foreach my $params (@$form_params){
	print '<table class="form" border="1">' . "\n";
	&print_form($params);			# forms
	print '</table>' . "\n";
}
print "<hr>\n";

#
#	Link of the spread sheet
#
print "<a href=\"$spread_sheet\">元データ(Spread Sheet)</a><br>" . "\n";
print '<table>' . "\n";
$head =  "<tr>";
for(my $i = 0; $i < scalar(@$DISPLAY_DEFS); $i++){
	my $item = $DISPLAY_DEFS->[$i]->{item}//"";
	my $width = $DISPLAY_DEFS->[$i]->{width}//0;
	$item =~ s/Evaluation/EV/;
	$head .= 	&print_item("<th bgcolor=\"gray\" width=\"$width\">", $item); 
}
$head .= "</tr>\n";
print $head . "\n";
my $last_date = "0000-00";
my @item_list = ();

my $na = {};
foreach my $k (@ITEM_LIST){
	$na->{$k} = "-";	# "&nbsp;"
}

#
#	Sorted Target (HIT) Record
#
my $month_no = 0;
$rn = 1;
foreach my $item (sort {$a->{"Display Date"} cmp $b->{"Display Date"}} @NENPYOU){
	#if($item->{Title} =~ /IT革命/){
	#	dp::dp join(",", $item->{Title}, $item->{URL}) . "<br>\n";
	#	my $ip = $NENPYOU[4];
	#	dp::dp "#####" . join(",", $ip->{Title}, $ip->{URL}) . "<br>\n";
	#}	
	$item->{"Display Date"} =~ /\d{4}-\d{2}/;
	my $item_date = $&;
	$item->{rn} = $rn++;
	if($item_date eq $last_date){		# for monthly base output
		push(@item_list, $item);		# set to print
		next;
	}
	#	output pushed items to @item_list
	my $cl = $table_color[$month_no % 2];
	foreach my $item (@item_list){
		print &row($item, $cl);
	}	
	$month_no++;

	#	output no taget data month
	foreach my $ym (&month_diff($last_date, $item_date)){
		#dp::dp ">>>> $ym" . "\n";
		$cl = $table_color[$month_no % 2];
		$na->{"Display Date"} = $ym . "-00";

		my $html = &gen_tag("<tr>", &print_item("<td bgcolor=\"$cl\">", &item_list($na, $DISPLAY_ITEMS_NO, 1)), {align => 1}) ; 
		print $html . "\n" if($EMPTY_MONTH);
		$month_no++;
	}

	@item_list = ($item);
	$last_date = $item_date;
}
if($#item_list >= 0){					# output final items in @item_list
	my $cl = $table_color[$month_no % 2];
	foreach my $item (@item_list){
		print &row($item, $cl);
	}	
}

print "</table>\n";
print "</body>\n";
print "</html>\n";

exit 0;


#
#	output one row as table (TR, TD)
#
sub	row
{
	my($item, $cl) = @_;

	#dp::dp join(",", $item->{Title}, $item->{URL}) . "<br>\n";
	my $url = $item->{URL}//"";
	my $title = $item->{Title}//"NO TITLE";
	if($url =~ /https*:/){
		$item->{Title} = "<a href=\"$url\" target=\"_blank\">$title</a>"; 
	}
	#dp::dp "$title url: [$url]\n";
	my $html = &gen_tag("<tr>", &print_item("<td bgcolor=\"$cl\">", &item_list($item, $DISPLAY_ITEMS_NO))) ; 
	return $html;
}

#
#	output missing month
#
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

#
#	Increment Month 
#
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
#	Force to Numeric Value
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

#
#	output Array of item list as HTML with $tag
#
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

#
#	output item list as HTML with $tag
#
sub	print_item
{
	my ($tag, @items, $p) = @_;
	$tag = $tag//$dlm;

	my $str = "";
	for(my $i = 0; $i <= $#items; $i++){
		my $v = $items[$i];
		my $aln = $DISPLAY_DEFS->[$i]->{align}//"";
		my $tgw = $tag;
		if(($p->{align}//"") && $aln){
			$tgw =~ s/\>/ align=\"$aln\"\>/;
		}
		my $it = &gen_tag($tgw, $v);
		#dp::dp "[$tag] [$it]<br>\n";
		$str .= $it;
	}
	return $str;
}

#
#	Pickup target col from data (a line)
#
sub	item_list
{
	my ($item, $targets) = @_;

	my @vals = ();
	for(my $i = 0; $i < $#ITEM_LIST; $i++){
		my $key = $ITEM_LIST[$i]//"-NONE $i-";
		push(@vals, $item->{$key}//"");
	}
	my @ww = ();
	foreach my $cl (@$targets){
		my $v = ($cl =~ /\D/) ? $item->{$cl}//" " : $vals[$cl];
		push(@ww, $v);
	}
	#dp::dp join(",", $#ww, @ww) . "<br>\n";
	return @ww;
}

#
#	<$tag> $str </$tag>
#
sub	gen_tag
{
	my($tag, $str) = @_;
	$str = $str//"";
	my $etag = $tag;
	$etag =~ s/\</\<\//;
	$etag =~ s/ .*>/>/;
	return ($tag . " $str " . $etag . "\n");
}

#
#	Generate Form Parameter from Form Defintion
#
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
			foreach my $g ("$NA:$NA", @group,){ # "$NA:$NA"){
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
	my $css = &get_css();

my $HTML_HEAD = <<_EOHTML_;
Content-type: text/html


<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title> #TITLE# </title>
<style>
$css
</style>
</head>
_EOHTML_

	$HTML_HEAD =~ s/#TITLE#/$title/g;
	return $HTML_HEAD;

}

#
#	Download JNSA Chronicle data from the google spread sheet 
#
sub	downlad_chroncile
{
	my $key = '1RGa0W19wC2NXOm4Fd_6eYlw_NPgbud2EbuU8aobZh2s';
	my $gid = '1801759358';
	my $format = 'tsv';
	my $fname = "./jnsa-nenpyou" . ".$format";

	my $url = "https://docs.google.com/spreadsheets/d/$key/export?gid=$gid&format=$format";
	my $cmd = "wget -O $fname '$url'";

	my $cwd = `pwd`;
	dp::dp "$cwd<br>\n" if($DEBUG);
	dp::dp "copy $fname, $fname.back<br>\n" if($DEBUG);
	copy($fname, "$fname.back");

	dp::dp $cmd . "<br>\n" if($DEBUG);
	system($cmd);

	if(0){
		print  "-" x 40 . "\n";

		open(FD, $fname) || die "$fname";
		my $ln = 0;
		while(<FD>){
			last if($ln++ > 20);
			print $_;
		}
		close(FD);
	}
	return 0;
}

#
#	for injection
#
sub	escape_html
{
	my ($str) = @_;

    $str =~ s/&/&amp;/go;
    $str =~ s/\"/&quot;/go; #" make emacs happy
    $str =~ s/>/&gt;/go;
    $str =~ s/</&lt;/go;

    $str =~ s/\|/&brvbar;/go;
    return $str;
}

sub	get_css
{
my $css = <<_EOSTYLE_;
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

return $css;
}
