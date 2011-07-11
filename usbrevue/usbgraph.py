#!/usr/bin/env python

import sys
from usbview import PcapThread
from usbrevue import Packet
from PyQt4 import Qt
from PyQt4.QtGui import *
from PyQt4.QtCore import QAbstractTableModel, QModelIndex, QVariant
import PyQt4.Qwt5 as Qwt


class BytePlot(Qwt.QwtPlot):
    def __init__(self, parent=None):
        Qwt.QwtPlot.__init__(self, parent)

        self.setCanvasBackground(Qt.Qt.white)
        self.alignScales()

        self.x = range(100)
        self.bytes = list()

        self.byteCurves = list()

        self.insertLegend(Qwt.QwtLegend(), Qwt.QwtPlot.BottomLegend)


    def alignScales(self):
        self.canvas().setFrameStyle(Qt.QFrame.Box | Qt.QFrame.Plain)
        self.canvas().setLineWidth(1)
        for i in range(Qwt.QwtPlot.axisCnt):
            scaleWidget = self.axisWidget(i)
            if scaleWidget:
                scaleWidget.setMargin(0)
            scaleDraw = self.axisScaleDraw(i)
            if scaleDraw:
                scaleDraw.enableComponent(
                    Qwt.QwtAbstractScaleDraw.Backbone, False)


    def new_packet(self, packet):
        if len(packet.data) > 0:
            if len(self.bytes) < len(packet.data):
                for i in range(len(packet.data) - len(self.bytes)):
                    self.bytes.append(list())
                    self.add_byte_curve(i)

            for i in range(len(packet.data)):
                self.bytes[i].append(packet.data[i])

            for i in range(len(self.bytes)):
                self.byteCurves[i].setData(self.x, self.bytes[i])

            self.replot()


    def add_byte_curve(self, i):
        self.byteCurves.append(Qwt.QwtPlotCurve('Byte ' + str(i)))
        self.byteCurves[-1].attach(self)
        self.byteCurves[-1].setPen(Qt.QPen(Qt.Qt.red))



class ByteModel(QAbstractTableModel):
    def __init__(self, parent=None):
        QAbstractTableModel.__init__(self, parent)

        self.bytes = []
        self.headers = {}


    def rowCount(self, parent = QModelIndex()):
        return 0 if parent.isValid() else len(self.bytes)


    def columnCount(self, parent = QModelIndex()):
        return 0 if parent.isValid() else len(self.headers)


    def data(self, index, role = Qt.Qt.DisplayRole):
        row = index.row()
        col = index.column()
        bytes = self.bytes[row]

        if role == Qt.Qt.DisplayRole:
            if isinstance(bytes, str):
                return bytes
            else:
                return bytes[col]
        elif role == Qt.Qt.UserRole:
            return QVariant(bytes)

        return QVariant()


    def headerData(self, section, orientation, role = Qt.Qt.DisplayRole):
        if role == Qt.Qt.DisplayRole and orientation == Qt.Qt.Horizontal:
            return self.headers[section]


    def new_packet(self, packet):
        l = len(self.bytes)
        self.beginInsertRows(QModelIndex(), l, l)
        self.bytes.append(packet.data)
        self.endInsertRows()



class ByteView(QTreeView):
    def __init__(self, parent=None):
        QTreeView.__init__(self, parent)

    def rowsInserted(self, parent, start, end):
        QTreeView.rowsInserted(self, parent, start, end)

        for row in xrange(start, end+1):
            idx = self.model().index(row, 0, parent)
            bytes = self.model().data(idx, Qt.Qt.UserRole).toPyObject()



class USBGraph(QApplication):
    def __init__(self, argv):
        QApplication.__init__(self, argv)
        self.w = QWidget()
        self.w.resize(800, 600)

        self.bytemodel = ByteModel()
        self.byteview = ByteView()
        self.byteview.setModel(self.bytemodel)
        self.byteplot = BytePlot()

        self.hb = QHBoxLayout()
        self.hb.addWidget(self.byteview)
        self.hb.addWidget(self.byteplot)

        self.w.setLayout(self.hb)
        self.w.show()

        self.pcapthread = PcapThread()
        self.pcapthread.dump_opened.connect(self.dump_opened)
        self.pcapthread.new_packet.connect(self.new_packet)
        self.pcapthread.start()

        self.dumper = None


    def dump_opened(self, dumper):
        self.dumper = dumper


    def new_packet(self, packet):
        self.byteplot.new_packet(packet)
        self.bytemodel.new_packet(packet)


if __name__ == "__main__":
    app = USBGraph(sys.argv)
    sys.exit(app.exec_())

