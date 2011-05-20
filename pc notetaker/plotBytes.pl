#!/usr/bin/perl

use warnings;
use strict;

use IO::Handle;
use Data::Dumper;

if ($#ARGV == -1) {
    print "Specify the max number of bytes in the stream and the byte(s) to be plotted. Use \"+\" to indicate that two bytes should be combined.\n";
    exit(0);
}

my $numberOfBytes = $ARGV[0] - 1;
my @bytesToPlot = ();
my $inputFile = "data.dat";
my $xWindow = 1000;
my $initialxWindow = $xWindow;
my $setYrange = 0;
my $ymin;
my $ymax;

for (my $argCnt = 1; $argCnt <= $#ARGV; $argCnt++) {
    my $arg = $ARGV[$argCnt];
    if ($arg eq "-yrange") {
	$argCnt++;
	if ($ARGV[$argCnt] =~ /((([0-9]|[A-Fa-f]) ?)+):((([0-9]|[A-Fa-f]) ?)+)/) {
	    $setYrange = 1;
	    $ymin = hex($1);
	    $ymax = hex($4);
	}
    } else {
	push @bytesToPlot, $arg;
    }
}

local *PIPE;
open(PIPE, "|gnuplot -persist") || die $!;
PIPE->autoflush;
print PIPE "set xtics\n";
print PIPE "set ytics\n";
#print PIPE "set autoscale\n";
if ($setYrange) {
    print PIPE "set yrange [$ymin:$ymax]\n";
}
print PIPE "set xrange [0:$initialxWindow]\n";
print PIPE "set format " . "y" . " \"%x\"\n";
print PIPE "set terminal x11 noraise\n";
print PIPE "set grid\n";
STDOUT->autoflush(1);
STDIN->blocking(0);

open(INPUTFILE, ">$inputFile") || die $!;
INPUTFILE->autoflush(1);

my $lineCount = 0;

my $replot = 0;

open(IN, "sudo ./device |") || die $!;
while (my $in = <IN>) {
    chomp($in);
    
    if($in =~ /^(([0-9]|[A-Fa-f]) ?)+$/) {
	print "$in\n";
	my @hexVals = split(/ /, $in);
	
	print INPUTFILE sprintf("%06d   ", $lineCount);

	foreach my $b (@bytesToPlot) {
	    if ($b =~ /^\d+$/) {
		if (defined($hexVals[$b])) {
		    print INPUTFILE sprintf("%03d ", hex($hexVals[$b]));
		} else {
		    print INPUTFILE "??? ";
		}
	    } elsif ($b =~ /^(\d+)\+(\d+)$/) {
	        if (defined($hexVals[$1]) && defined($hexVals[$2])) {
		    print INPUTFILE sprintf("%06d ", hex($hexVals[$1])*128 + hex($hexVals[$2]));
		} else {
		    print INPUTFILE "?????? ";
		}
	    } elsif ($b =~ /^(\d+)\+(\d+)\+(\d+)$/) {
		if (defined($hexVals[$1]) &&
		    defined($hexVals[$2]) &&
		    defined($hexVals[$3])) {
		    print INPUTFILE sprintf("%09d ",
					    hex($hexVals[$1])*128*128 +
					    hex($hexVals[$2])*128 +
					    hex($hexVals[$3]));
		} else {
		    print INPUTFILE "????????? ";
		}
	    } elsif ($b =~ /^(\d+)\+(\d+)\+(\d+)\+(\d+)$/) {
		if (defined($hexVals[$1]) &&
		    defined($hexVals[$2]) &&
		    defined($hexVals[$3]) &&
		    defined($hexVals[$4])) {
		    print INPUTFILE sprintf("%012d ",
					     hex($hexVals[$1])*128*128*128 +
					     hex($hexVals[$2])*128*128 +
					     hex($hexVals[$3])*128 +
					     hex($hexVals[$4]));
		} else {
		    print INPUTFILE "???????????? ";
		}
	    }
	}
	print INPUTFILE "\n";
	$lineCount++;
	if ($lineCount > $initialxWindow) {
	    print PIPE "set xrange [" . ($lineCount-$xWindow) . ":" . ($lineCount) . "]\n";
	}
    }
    
    if ($replot) {
	print PIPE "replot\n";
    } else {
	sleep 1;
	print PIPE "plot \"$inputFile\" using 1:2 title 'Byte $bytesToPlot[0]' with points pointtype 7 pointsize 1";
	for (my $i = 1; $i <= $#bytesToPlot; $i++) {
	    print PIPE ", \"$inputFile\" using 1:" . ($i + 2) . " title 'Byte $bytesToPlot[$i]' with points pointtype 7 pointsize 1";
	}
	print PIPE "\n";
	$replot = 1;
    }
}
# print PIPE "exit;\n";
# close PIPE;
# close INPUTFILE;

