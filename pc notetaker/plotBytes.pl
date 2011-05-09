#!/usr/bin/perl

use warnings;
use strict;

use Tk;
use Tk::LineGraph;
use Graphics::GnuplotIF;

my @bytes;
my @checkbuttons;
my $getStdin = 1;

my $mw = new MainWindow;
my $startButton = $mw->Button(-text =>"Start Monitoring",-command=>\&start)->pack();
my $stopButton = $mw->Button(-text=>"Stop Monitoring", -command=>\&stop)->pack();
my $exitButton = $mw->Button(-text=>"Exit", -command=> sub { exit(0); })->pack();
my $frame = $mw->Frame()->pack();

MainLoop;

exit(0);

sub start {
    @bytes = ();

    $frame->destroy;
    $frame = $mw->Frame()->pack();

    #open($pipe, 'sudo ./device |') || die $!;

    $mw->fileevent(\*STDIN, readable => \&read);
}

sub read {
        $_ = <STDIN>;
        print;
        # blank lines mean a new sequence
        if ($_ !~ /^\s*$/) {
            # split line into hex values
        chomp($_);
        my @hexVals = split(/ /, $_);

        # check that there is an array for every byte in this line, and add one if there is not
        if (scalar @bytes < scalar @hexVals) {
            for (my $i = scalar @bytes; $i < scalar @hexVals; $i++) {
                push @bytes, [my @tmp];
            }
        }

        # add the hex values to the appropriate arrays. add '  ' if a byte does not have a hex value in this line
        for (my $i = 0; $i < scalar @bytes; $i++) {
            if (defined $hexVals[$i]) {
                my $decimalVal = sprintf("%02d", hex($hexVals[$i]));
                push @{$bytes[$i]}, $decimalVal;
            } else {
                push @{$bytes[$i]}, '  ';
            }
        }
        }

        
}

sub stop {
    $#checkbuttons = scalar @bytes - 1;

    $startButton->update;
    
    $frame->Label(-text=>"Select byte(s) to graph:")->pack();
    for (my $i = 0; $i < scalar @bytes; $i++) {
        my $cb = $frame->Checkbutton(-text=>"$i", -variable=>\$checkbuttons[$i])->pack();
        $cb->deselect();
    }
    $frame->Button(-text=>"Plot", -command=>\&plot)->pack();
    $frame->update;
        
}

sub plot {
    # get the max and min values of the bytes
    my $max = 0;
    my $min = 255;
    for (my $i = 0; $i < scalar @checkbuttons; $i++) {
        if ($checkbuttons[$i] == 1) {
            foreach my $value (@{$bytes[$i]}) {
                if ($value ne "  " && $value > $max) {
                    $max = $value;
                }
                if ($value ne "  " && $value < $min) {
                    $min = $value;
                }
            }
        }
    }

    my @x = (0 .. (scalar @{$bytes[0]}));
    my $gnuPlotCmd = '$plot->gnuplot_plot_xy_style(\@x, ';
    my @gnuByteTitles;
    for (my $i = 0; $i < scalar @checkbuttons; $i++) {
        if ($checkbuttons[$i] == 1) {
            
            $gnuPlotCmd .= '{\'y_values\' => \@{$bytes[' . $i . ']}, \'style_spec\' => "points pointtype 7 pointsize 0.5"}, ';
            push @gnuByteTitles, "byte " . $i;
        }
    }
    chop($gnuPlotCmd);
    chop($gnuPlotCmd);
    $gnuPlotCmd .= ");";

    my $plot = Graphics::GnuplotIF->new(style => 'linepoints',
                                    title => "Byte Values",
                                    xlabel => "Message number",
                                    ylabel => "Hex value");
    $plot->gnuplot_cmd( 'set output', 'set key outside top', 'set key box linestyle 1', 'set xtics 1', 'set ytics ' . $min . ',8', 'set format y "%02x"', 'set grid' );
    $plot->gnuplot_set_plot_titles(@gnuByteTitles);
    eval $gnuPlotCmd;
    $plot->gnuplot_cmd('pause mouse');
}

exit(0);
