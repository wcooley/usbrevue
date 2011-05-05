#!/usr/bin/env python
import sys
from PyQt4.QtGui import *
from PyQt4.QtCore import QThread, pyqtSignal
from string import split
from math import pi, sin, asin, cos

class DrawWidget(QWidget):
  def __init__(self):
    QWidget.__init__(self)
    self.coords = []
    self.pen = QPen()
    self.pen.setWidth(3)

  def paintEvent(self, ev):
    painter = QPainter(self)
    painter.setPen(self.pen)
    for [x,y] in self.coords:
      painter.drawPoint(x, y)

  def new_coord(self, x, y):
    self.coords.append([self.width()/2 + x, y])
    self.update()


class CoordGen(QThread):
  new_coord = pyqtSignal(int, int)

  def run(self):
    lastr = 0
    while 1:
      line = split(raw_input())
      # still need to figure out 0xdb
      if len(line) >= 11 and (line[0] == "dd" or line[0] == "dc"):
        # both coordinate column pairs only use the lower 7 bits
        # e.g., 0x377f + 1 = 0x3800
        theta = (int(line[6], 16) << 7) | int(line[7],  16)
        # we don't always get bytes 11-12, so just reuse the last value
        r = lastr
        if len(line) >= 13:
          r = (int(line[11], 16) << 7) | int(line[12], 16) 
          lastr = r

        # these transformations came from a linear regression of some sloppy
        # measurements--we can do better
        theta = theta*-0.000650246 + 9.3338838923 # radians
        r = r*-0.0026145511 + 29.7896097057 # inches

        # this should hopefully give x and y, in inches, relative to the center
        # of the device
        theta = pi - theta - asin(2 * sin(theta)/r)
        y = r*sin(theta) 
        x = -r*cos(theta) + 2
        print x, y
        # just assume 90 dpi for now
        self.new_coord.emit(x*90, y*90)


a = QApplication(sys.argv)
w = DrawWidget()
w.resize(800, 600)
w.show()
cg = CoordGen()
cg.new_coord.connect(w.new_coord)
cg.start()
sys.exit(a.exec_())

