#!/usr/bin/env python

import sys
import pcapy
from usbrevue import Packet
from PyQt4.QtCore import Qt, QThread, QVariant, pyqtSignal, QAbstractTableModel, QModelIndex
from PyQt4.QtGui import *


class PcapThread(QThread):
  """ Thread responsible for reading pcap data from input and signalling
 arriving packets. """
  new_packet = pyqtSignal(object)
  eof = pyqtSignal()
  dump_opened = pyqtSignal(object)

  def __init__(self):
    QThread.__init__(self)

  def run(self):
    pcap = pcapy.open_offline('-')
    # don't output anything unless we're being piped/redirected
    if not sys.stdout.isatty():
      out = pcap.dump_open('-')
      self.dump_opened.emit(out)

    while 1:
      (hdr, pack) = pcap.next()
      if hdr is None:
        self.eof.emit()
        break
      self.new_packet.emit(Packet(hdr, pack))




class PacketModel(QAbstractTableModel):
  """ Qt model for packet data. """
  def __init__(self, parent = None):
    QAbstractTableModel.__init__(self, parent)
    self.packets = []
    # this is likely to change
    self.headers = ["Timestamp", "URB id", "Address", "Data"]
    # timestamp of the first received packet
    self.first_ts = 0

  def rowCount(self, parent = QModelIndex()):
    return 0 if parent.isValid() else len(self.packets)

  def columnCount(self, parent = QModelIndex()):
    return 0 if parent.isValid() else len(self.headers)

  def data(self, index, role = Qt.DisplayRole):
    row = index.row()
    col = index.column()
    pack = self.packets[row]

    if role == Qt.DisplayRole:
      #TODO define constants for column numbers
      if col == 0:
        return "%d.%06d" % (pack.ts_sec - self.first_ts, pack.ts_usec)
      elif col == 1:
        return "%016X" % pack.id
      elif col == 2:
        return "%d:%d:%x (%s%s)" % (pack.busnum, pack.devnum, pack.epnum,
                                    "ZICB"[pack.xfer_type], "oi"[pack.epnum>>8])
      elif col == 3:
        return ' '.join(map(lambda x: "%02X" % x, pack.data))
    elif role == Qt.FontRole and col in [1, 2, 3]:
      return QFont("monospace")
        
    return QVariant()

  def headerData(self, section, orientation, role = Qt.DisplayRole):
    if role == Qt.DisplayRole and orientation == Qt.Horizontal:
      return self.headers[section]
    return QVariant()

  def new_packet(self, pack):
    l = len(self.packets)
    self.first_ts = self.first_ts or pack.ts_sec
    self.beginInsertRows(QModelIndex(), l, l)
    self.packets.append(pack)
    self.endInsertRows()




class PacketFilterProxyModel(QSortFilterProxyModel):
  """ Proxy model for filtering displayed packets. """
  def __init__(self, parent = None):
    QSortFilterProxyModel.__init__(self, parent)
    self.expr = 'True'

  def set_filter(self, e):
    self.expr = 'True' if len(e)==0 else str(e)
    self.invalidateFilter()

  def filterAcceptsRow(self, source_row, source_parent):
    # TODO it would probably be better form to define a new role
    # and use sourceModel().data() to get the packet
    packet = self.sourceModel().packets[source_row]
    try:
      return eval(self.expr, packet.__dict__)
    except:
      return False




class FilterWidget(QWidget):
  new_filter = pyqtSignal(str)

  def __init__(self, parent = None):
    QWidget.__init__(self, parent)
    self.lineedit = QLineEdit()
    self.applybtn = QPushButton("&Apply")
    self.clearbtn = QPushButton("&Clear")
    self.hb = QHBoxLayout()
    self.hb.addWidget(QLabel("Filter"))
    self.hb.addWidget(self.lineedit)
    self.hb.addWidget(self.applybtn)
    self.hb.addWidget(self.clearbtn)
    self.setLayout(self.hb)
    self.applybtn.clicked.connect(self.update_filter)
    self.clearbtn.clicked.connect(self.clear_filter)
    self.lineedit.returnPressed.connect(self.update_filter)
    
  def update_filter(self):
    #TODO validation
    self.new_filter.emit(str(self.lineedit.text()))

  def clear_filter(self):
    self.lineedit.setText("")
    self.update_filter()




class USBView(QApplication):
  def __init__(self, argv):
    QApplication.__init__(self, argv)
    self.w = QWidget()
    self.w.resize(800, 600)

    self.packetmodel = PacketModel()
    self.proxy = PacketFilterProxyModel()
    self.proxy.setSourceModel(self.packetmodel)
    self.packetview = QTreeView()
    self.packetview.setRootIsDecorated(False)
    self.packetview.setModel(self.proxy)
    self.packetview.setSelectionMode(QAbstractItemView.ExtendedSelection)
    self.packetview.setUniformRowHeights(True)

    self.filterpane = FilterWidget()
    self.filterpane.new_filter.connect(self.proxy.set_filter)

    self.vb = QVBoxLayout()
    self.vb.addWidget(self.filterpane)
    self.vb.addWidget(self.packetview)
    self.w.setLayout(self.vb)
    self.w.show()

    self.pcapthread = PcapThread()
    self.pcapthread.new_packet.connect(self.packetmodel.new_packet)
    self.pcapthread.dump_opened.connect(self.dump_opened)
    self.pcapthread.start()

    self.dumper = None

  def dump_opened(self, dumper):
    self.dumper = dumper




app = USBView(sys.argv)
sys.exit(app.exec_())

