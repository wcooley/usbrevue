#!/usr/bin/env python

import sys
from usbview import PcapThread
from usbrevue import Packet
from PyQt4 import Qt
from PyQt4.QtGui import *
from PyQt4.QtCore import QAbstractTableModel, QModelIndex, QVariant, QString, QByteArray, pyqtSignal
import PyQt4.Qwt5 as Qwt
import numpy as np


class ByteModel(QAbstractTableModel):
    bytes_added = pyqtSignal()
    row_added = pyqtSignal()
    col_added = pyqtSignal()

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
        val = bytes[col][row-1]

        if role == Qt.Qt.DisplayRole:
            if isinstance(val, str):
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
                else:
                    self.cb_states[col] = 0
            return True
        return False

    def headerData(self, section, orientation, role = Qt.Qt.DisplayRole):
        if role == Qt.Qt.DisplayRole:
            if orientation == Qt.Qt.Horizontal:
                return section
        return QVariant()

    def flags(self, index):
        if index.row() == 0:
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
            self.bytes_added.emit()


class ByteDelegate(QItemDelegate):
    def __init__(self, parent=None, *args):
        QItemDelegate.__init__(self, parent, *args)

    def paint(self, painter, option, index):
            QItemDelegate.paint(self, painter, option, index)

    def createEditor(self, parent, option, index):
        if index.isValid() and index.column() == 0:
            return QCheckBox(parent)
        else:
            return QItemDelegate.createEditor(self, parent, option, index)

    def setEditorData(self, editor, index):
        if index.isValid() and index.column() == 0:
            value = index.model().data(index, Qt.Qt.DisplayRole)
        else:
            QItemDelegate.setEditorData(self, editor, index)

    def setModelData(self, editor, model, index):
        if index.isValid() and index.column() == 0:
            self.cb = QCheckBox(editor)
            if (self.cb.checkState() == Qt.Qt.Checked):
                self.value = 'Y'
            else:
                self.value = 'N'
        else:
            QItemDelegate.setModelData(self, editor, model, index)

    def updateEditorGeometry(self, editor, option, index):
        QItemDelegate.updateEditorGeometry(self, editor, option, index)
        

class ByteView(QTableView):
    def __init__(self, parent=None):
        QTableView.__init__(self, parent)

    def col_added(self):
        self.resizeColumnsToContents()


class BytePlot(Qwt.QwtPlot):
    def __init__(self, *args):
        Qwt.QwtPlot.__init__(self, *args)

        self.setCanvasBackground(Qt.Qt.white)
        self.alignScales()

        self.x_range = 200

        self.curve = ByteCurve("Byte 1")
        self.curve.attach(self)

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

    def bytes_added(self):
        mask = [c >= 0 for c in bytes[1]]
        l = len(bytes[1])
        if l > self.x_range:
            l = len(bytes[1])
            self.curve.setData(ByteData(range(l)[l-self.x_range:l], bytes[1][l-self.x_range:l], mask[l-self.x_range:l]))
            self.setAxisScale(2, l-self.x_range, l)
        else:
            self.curve.setData(ByteData(range(l)[:self.x_range], bytes[1][:self.x_range], mask[:self.x_range]))

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

    def boundingRect(self):
        xmax = self.__x[self.__mask].max()
        xmin = self.__x[self.__mask].min()
        ymax = self.__y[self.__mask].max()
        ymin = self.__y[self.__mask].min()

        return Qt.QRectF(xmin, ymin, xmax-xmin, ymax-ymin)


class ByteCurve(Qwt.QwtPlotCurve):
    def __init__(self, title=None):
        Qwt.QwtPlotCurve.__init__(self, title)

    def draw(self, painter, xMap, yMap, rect):
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

class USBGraph(QApplication):
    def __init__(self, argv):
        QApplication.__init__(self, argv)
        self.w = QWidget()
        self.w.resize(800, 600)

        self.bytemodel = ByteModel()
        self.byteview = ByteView()
        self.bytedelegate = ByteDelegate()
        self.byteview.setModel(self.bytemodel)
        self.byteview.setItemDelegate(self.bytedelegate)
        self.byteplot = BytePlot()

        self.bytemodel.bytes_added.connect(self.bytes_added)
        self.bytemodel.col_added.connect(self.byteview.col_added)

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

