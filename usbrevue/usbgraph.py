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

        if (role == Qt.Qt.DisplayRole):
            #if len(bytes) > col and len(bytes[col]) > row:
            if isinstance(val, str):
                return val
            else:
                return "%02X" % val
            # return QString('Row%1, Column%2').arg(index.row() + 1).arg(index.column() + 1)
        return QVariant()

    def headerData(self, section, orientation, role = Qt.Qt.DisplayRole):
        if role == Qt.Qt.DisplayRole:
            if orientation == Qt.Qt.Horizontal:
                return section
        return QVariant()

    def new_packet(self, packet):
        if len(packet.data) > 0:
            print packet.data
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
                    else:
                        bytes.append(list('-' * len(bytes[0])))
                self.endInsertColumns()
            self.beginInsertRows(QModelIndex(), l, l)

            offset = 0
            for b in packet.data:
                bytes[offset].append(b)
                offset += 1
            while offset < len(bytes):
                bytes[offset].append('-')
                offset += 1
            self.endInsertRows()


class ByteView(QTableView):
    def __init__(self, parent=None):
        QTableView.__init__(self, parent)



class USBGraph(QApplication):
    def __init__(self, argv):
        QApplication.__init__(self, argv)
        self.w = QWidget()
        self.w.resize(800, 600)

        self.bytemodel = ByteModel()
        self.byteview = ByteView()
        self.byteview.setModel(self.bytemodel)

        self.hb = QHBoxLayout()
        self.hb.addWidget(self.byteview)

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
        self.bytemodel.new_packet(packet)



bytes = list()


if __name__ == "__main__":
    app = USBGraph(sys.argv)
    sys.exit(app.exec_())

