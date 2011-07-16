#!/usr/bin/env python

import sys
from usbview import PcapThread
from usbrevue import Packet
from PyQt4 import Qt
from PyQt4.QtGui import *
from PyQt4.QtCore import QAbstractTableModel, QModelIndex, QVariant, QString, QByteArray, pyqtSignal, QTimer
import PyQt4.Qwt5 as Qwt
import numpy as np
import random


class ByteModel(QAbstractTableModel):
    row_added = pyqtSignal()
    col_added = pyqtSignal()
    cb_checked = pyqtSignal(int)
    cb_unchecked = pyqtSignal(int)

    def __init__(self, parent=None):
        QAbstractTableModel.__init__(self, parent)

        self.cb_states = list()


    def rowCount(self, parent = QModelIndex()):
        if len(bytes) > 0:
            return len(bytes[0])
        else:
            return 0

    def columnCount(self, parent = QModelIndex()):
        return len(bytes)

    def data(self, index, role = Qt.Qt.DisplayRole):
        row = index.row()
        col = index.column()
        val = bytes[col][row]

        if role == Qt.Qt.DisplayRole:
            if row == len(bytes[0]) - 1:
                return QVariant()
            elif isinstance(val, str):
                return val
            else:
                if val == -1:
                    return '-'
                else:
                    return "%02X" % val
        elif role == Qt.Qt.CheckStateRole and row == 0:
            return QVariant(self.cb_states[col])
        return QVariant()

    def setData(self, index, value, role = Qt.Qt.EditRole):
        if role == Qt.Qt.CheckStateRole:
            row = index.row()
            col = index.column()
            if row == 0:
                if self.cb_states[col] == 0:
                    self.cb_states[col] = 2
                    self.cb_checked.emit(col)
                else:
                    self.cb_states[col] = 0
                    self.cb_unchecked.emit(col)
            return True
        return False

    def headerData(self, section, orientation, role = Qt.Qt.DisplayRole):
        if role == Qt.Qt.DisplayRole:
            if orientation == Qt.Qt.Horizontal:
                return section
        return QVariant()

    def flags(self, index):
        if index.row() == len(bytes[0]) - 1:
            return Qt.Qt.ItemIsUserCheckable | Qt.Qt.ItemIsEnabled
        else:
            return Qt.Qt.ItemIsEnabled | Qt.Qt.ItemIsSelectable

    def new_packet(self, packet):
        if len(packet.data) > 0:
            if len(bytes) > 0:
                l = len(bytes[0])
            else:
                l = 0
            w = len(bytes)

            first_row = True if len(bytes) == 0 else False
            if len(packet.data) > len(bytes):
                self.beginInsertColumns(QModelIndex(), w, max(len(bytes), len(packet.data) - 1))
                for i in range(len(packet.data) - len(bytes)):
                    if first_row:
                        bytes.append(list())
                        self.cb_states.append(0)
                    else:
                        bytes.append([-1] * len(bytes[0]))
                        self.cb_states.append(0)
                self.endInsertColumns()
                self.col_added.emit()

            self.beginInsertRows(QModelIndex(), l, l)
            offset = 0
            for b in packet.data:
                bytes[offset].append(b)
                offset += 1
            while offset < len(bytes):
                bytes[offset].append(-1)
                offset += 1
            self.endInsertRows()
            self.row_added.emit()


class ByteView(QTableView):
    def __init__(self, parent=None):
        QTableView.__init__(self, parent)

        self.autoscroll_timer = QTimer(self)
        self.autoscroll_timer.setSingleShot(True)
        self.autoscroll_timer.timeout.connect(self.scrollToBottom)

    def col_added(self):
        self.resizeColumnsToContents()

    def row_added(self):
        if not self.autoscroll_timer.isActive():
            self.autoscroll_timer.start(50)


class BytePlot(Qwt.QwtPlot):
    def __init__(self, *args):
        Qwt.QwtPlot.__init__(self, *args)

        self.setCanvasBackground(Qt.Qt.white)
        self.alignScales()

        self.x_range = 200

        random.seed()

        #self.curve = ByteCurve("Byte 1")
        #self.curve.attach(self)
        self.curves = {}

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
                scaleDraw.enableComponent(Qwt.QwtAbstractScaleDraw.Backbone, False)

    def row_added(self):
        l = len(bytes[0])
        for c in self.curves:
            mask = [j >= 0 for j in bytes[c]]
            if l > self.x_range:
                self.curves[c].setData(ByteData(range(l)[l-self.x_range:l], bytes[c][l-self.x_range:l], mask[l-self.x_range:l]))
                self.setAxisScale(2, l-self.x_range, l)
            else:
                self.curves[c].setData(ByteData(range(l)[:self.x_range], bytes[c][:self.x_range], mask[:self.x_range]))

        self.replot()

    def cb_checked(self, column):
        if column not in self.curves:
            l = len(bytes[0])
            mask = [j >= 0 for j in bytes[column]]
            self.curves[column]= ByteCurve("Byte " + str(column))
            if l > self.x_range:
                self.curves[column].setData(ByteData(range(l)[l-self.x_range:l], bytes[column][l-self.x_range:l], mask[l-self.x_range:l]))
                self.setAxisScale(2, l-self.x_range, l)
            else:
                self.curves[column].setData(ByteData(range(l)[:self.x_range], bytes[column][:self.x_range], mask[:self.x_range]))

            color = QColor()
            color.setHsv(random.randint(0,255), random.randint(0,255), random.randint(0,255))
            self.curves[column].setPen(QPen(QBrush(color), 2))
            self.curves[column].setStyle(Qwt.QwtPlotCurve.Dots)

        self.curves[column].attach(self)

        self.replot()

    def cb_unchecked(self, column):
        self.curves[column].detach()

        self.replot()

class ByteData(Qwt.QwtArrayData):
    def __init__(self, x, y, mask):
        Qwt.QwtArrayData.__init__(self, x, y)
        self.__mask = np.asarray(mask, bool)
        self.__x = np.asarray(x)
        self.__y = np.asarray(y)

    def copy(self):
        return self

    def mask(self):
        return self.__mask
    """
    def boundingRect(self):
        xmax = self.__x[self.__mask].max()
        xmin = self.__x[self.__mask].min()
        ymax = self.__y[self.__mask].max()
        ymin = self.__y[self.__mask].min()

        return Qt.QRectF(xmin, ymin, xmax-xmin, ymax-ymin)
    """

class ByteCurve(Qwt.QwtPlotCurve):
    def __init__(self, title=None):
        Qwt.QwtPlotCurve.__init__(self, title)

    def draw(self, painter, xMap, yMap, rect):
        try:
            indices = np.arange(self.data().size())[self.data().mask()]
            fs = np.array(indices)
            fs[1:] -= indices[:-1]
            fs[0] = 2
            fs = indices[fs > 1]
            ls = np.array(indices)
            ls[:-1] -= indices[1:]
            ls[-1] = -2
            ls = indices[ls < -1]
            for first, last in zip(fs, ls):
                Qwt.QwtPlotCurve.drawFromTo(self, painter, xMap, yMap, first, last)
        except AttributeError:
            pass

class USBGraph(QApplication):
    def __init__(self, argv):
        QApplication.__init__(self, argv)
        self.w = QWidget()
        self.w.resize(800, 600)

        self.bytemodel = ByteModel()
        self.byteview = ByteView()
        self.byteview.setModel(self.bytemodel)
        self.byteplot = BytePlot()

        self.bytemodel.row_added.connect(self.byteplot.row_added)
        self.bytemodel.row_added.connect(self.byteview.row_added)
        self.bytemodel.col_added.connect(self.byteview.col_added)
        self.bytemodel.cb_checked.connect(self.byteplot.cb_checked)
        self.bytemodel.cb_unchecked.connect(self.byteplot.cb_unchecked)

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

    def new_packet(self, packet):
        self.bytemodel.new_packet(packet)

    def bytes_added(self):
        self.byteplot.bytes_added()

    def dump_opened(self, dumper):
        pass



bytes = list()


if __name__ == "__main__":
    app = USBGraph(sys.argv)
    sys.exit(app.exec_())

