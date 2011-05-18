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
my $xWindow = 50;
my $initialxWindow = $xWindow;

for (my $argCnt = 1; $argCnt <= $#ARGV; $argCnt++) {
    my $arg = $ARGV[$argCnt];
    push @bytesToPlot, $arg;
}

local *PIPE;
open(PIPE, "|gnuplot -persist") || die $!;
PIPE->autoflush;
print PIPE "set xtics\n";
print PIPE "set ytics\n";
print PIPE "set autoscale\n";
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

while (my $in = <STDIN>) {
    chomp($in);
    
    unless($in =~ /^\s*$/) {
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
	    }
	}
#	for (my $i = 0; $i < $numberOfBytes; $i++) {
	    #if (defined($hexVals[$i])) {
	#	print INPUTFILE sprintf("%03d ", hex($hexVals[$i]));
	#    } else {
#		print INPUTFILE "??? ";
#	    }
#	}
	print INPUTFILE "\n";
	$lineCount++;
	if ($lineCount > $initialxWindow) {
	    print PIPE "set xrange [" . ($lineCount-$xWindow) . ":" . ($lineCount) . "]\n";
	}
    }
    
    if ($replot) {
	print PIPE "replot\n";
    } else {
	print PIPE "plot \"$inputFile\" using 1:2 title 'Byte $bytesToPlot[0]' with points pointtype 7 pointsize 1";
	for (my $i = 1; $i <= $#bytesToPlot; $i++) {
	    print PIPE ", \"$inputFile\" using 1:" . ($i + 2) . " title 'Byte $bytesToPlot[$i]' with points pointtype 7 pointsize 1";
	}
	print PIPE "\n";
	$replot = 1;
    }

    #print PIPE "pause mouse\n";
}

# print PIPE "exit;\n";
# close PIPE;
# close INPUTFILE;

