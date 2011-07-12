#!/usr/bin/env python

import sys
from usbview import PcapThread
from usbrevue import Packet
from PyQt4 import Qt
from PyQt4.QtGui import *
from PyQt4.QtCore import QAbstractTableModel, QModelIndex, QVariant, QString, QByteArray
import PyQt4.Qwt5 as Qwt


class ByteModel(QAbstractTableModel):
    def __init__(self, parent=None):
        QAbstractTableModel.__init__(self, parent)


    def rowCount(self, parent = QModelIndex()):
        return 100

    def columnCount(self, parent = QModelIndex()):
        return 4

    def data(self, index, role = Qt.Qt.DisplayRole):
        row = index.row()
        col = index.column()

        if (role == Qt.Qt.DisplayRole):
            if len(bytes) > col and len(bytes[col]) > row:
                return QVariant(bytes[col][row])
                # return QString('Row%1, Column%2').arg(index.row() + 1).arg(index.column() + 1)
        return QVariant()

    def headerData(self, section, orientation, role = Qt.Qt.DisplayRole):
        if (role == Qt.Qt.DisplayRole):
            if (orientation == Qt.Qt.Horizontal):
                if section == 0:
                    return QString("first")
                elif section == 1:
                    return QString("second")
                elif section == 2:
                    return QString("third")
        return QVariant()




class ByteView(QTableView):
    def __init__(self, parent=None):
        QTableView.__init__(self, parent)

    def new_packet(self, packet):
        if len(packet.data) > 0:
            if len(bytes) < len(packet.data):
                for i in range(len(packet.data) - len(bytes)):
                    bytes.append(list())
                    
            for i in range(len(packet.data)):
                bytes[i].append(packet.data[i])



class BytePlot(Qwt.QwtPlot):
    def __init__(self, parent=None):
        Qwt.QwtPlot.__init__(self, parent)

        self.setCanvasBackground(Qt.Qt.white)
        self.alignScales()

        self.x = range(100)
        
        self.byteCurves = list()

        self.insertLegend(Qwt.QwtLegend(), Qwt.QwtPlot.BottomLegend)


    def setModel(self, model):
        self.model = model


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
            if len(self.byteCurves) < len(packet.data):
                for i in range(len(packet.data) - len(self.byteCurves)):
                    self.add_byte_curve(i)

            for i in range(len(bytes)):
                self.byteCurves[i].setData(self.x, bytes[i])

            self.replot()


    def add_byte_curve(self, i):
        self.byteCurves.append(Qwt.QwtPlotCurve('Byte ' + str(i)))
        self.byteCurves[-1].attach(self)
        self.byteCurves[-1].setPen(Qt.QPen(Qt.Qt.red))



class USBGraph(QApplication):
    def __init__(self, argv):
        QApplication.__init__(self, argv)
        self.w = QWidget()
        self.w.resize(800, 600)

        self.bytemodel = ByteModel()
        self.byteview = ByteView()
        self.byteview.setModel(self.bytemodel)
        self.byteplot = BytePlot()
        self.byteplot.setModel(self.bytemodel)

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
        self.byteview.new_packet(packet)



bytes = list()


if __name__ == "__main__":
    app = USBGraph(sys.argv)
    sys.exit(app.exec_())

