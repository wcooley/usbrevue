#!/usr/bin/env python

import sys
import pcapy
from usbrevue import Packet
from PyQt4.QtCore import Qt, QThread, QVariant, pyqtSignal, \
                         QAbstractTableModel, QModelIndex, \
                         QPersistentModelIndex, QTimer
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
        if sys.stdin.isatty():
            return
        pcap = pcapy.open_offline('-')
        # don't output anything unless we're being piped/redirected
        if not sys.stdout.isatty():
            out = pcap.dump_open('-')
            sys.stdout.flush()
            self.dump_opened.emit(out)

        while 1:
            (hdr, pack) = pcap.next()
            if hdr is None:
                self.eof.emit()
                break
            self.new_packet.emit(Packet(hdr, pack))




# column indexes for packet model data
TIMESTAMP_COL = 0
URB_COL = 1
ADDRESS_COL = 2
DATA_COL = 3
NUM_COLS = 4


class PacketModel(QAbstractTableModel):
    """ Qt model for packet data. """
    def __init__(self, parent = None):
        QAbstractTableModel.__init__(self, parent)
        self.packets = []
        self.headers = {TIMESTAMP_COL: "Timestamp",
                        URB_COL: "URB id",
                        ADDRESS_COL: "Address",
                        DATA_COL: "Data"}
        # timestamp of the first received packet
        self.first_ts = 0

    def rowCount(self, parent = QModelIndex()):
        return 0 if parent.isValid() else len(self.packets)

    def columnCount(self, parent = QModelIndex()):
        return 0 if parent.isValid() else NUM_COLS

    def data(self, index, role = Qt.DisplayRole):
        row = index.row()
        col = index.column()
        pack = self.packets[row]

        if role == Qt.DisplayRole:
            if col == TIMESTAMP_COL:
                return "%d.%06d" % (pack.ts_sec - self.first_ts, pack.ts_usec)
            elif col == URB_COL:
                return "%016X" % pack.urb
            elif col == ADDRESS_COL:
                return "%d:%d:%x (%s%s)" % (pack.busnum, pack.devnum, pack.epnum,
                                            "ZICB"[pack.xfer_type],
                                            "oi"[pack.epnum >> 7])
            elif col == DATA_COL:
                return ' '.join(map(lambda x: "%02X" % x, pack.data))
        elif role == Qt.FontRole and col in [URB_COL, ADDRESS_COL, DATA_COL]:
            return QFont("monospace")
        elif role == Qt.UserRole: # packet object
            return QVariant(self.packets[row])
 
        return QVariant()

    def setData(self, index, value, role = Qt.EditRole):
        if role != Qt.EditRole or index.column() != DATA_COL:
            return False
        datastr = str(value.toString())
        try:
            data = map(lambda b: int(b, 16), datastr.split())
        except Exception:
            return False
        self.packets[index.row()].data = data
        self.dataChanged.emit(index, index)
        return True
        
    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return QVariant()

    def flags(self, index):
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if index.column() == DATA_COL:
            flags = flags | Qt.ItemIsEditable
        return flags

    def removeRows(self, first, count, parent = None):
        last = first + count - 1
        self.beginRemoveRows(QModelIndex(), first, last)
        self.packets = self.packets[:first] + self.packets[last+1:]
        self.endRemoveRows()
        return True

    def clear(self):
        self.beginResetModel()
        self.packets = []
        self.first_ts = 0
        self.endResetModel()

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
        self.expr = str(e) or 'True'
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        index = self.sourceModel().index(source_row, 0, source_parent)
        packet = self.sourceModel().data(index, Qt.UserRole).toPyObject()
        try:
            return bool(eval(self.expr, packet.field_dict))
        except Exception:
            return False

    def clear(self):
        self.sourceModel().clear()




class HexEditDelegate(QItemDelegate):
    """ Delegate enabling editing of packet payload """
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        pack = index.model().data(index, Qt.UserRole).toPyObject()
        # refuse editing if there's no existing data
        if not pack.data:
            return
        # only accept a series of hex character pairs of the same length
        # as the existing data. '>' forces uppercase.
        editor.setInputMask('>' + ' '.join(["HH"] * len(pack.data)))
        editor.installEventFilter(self)
        editor.setFont(QFont("monospace"))
        return editor

    def setEditorData(self, editor, index):
        text = index.model().data(index)
        editor.setText(text.toString())

    def setModelData(self, editor, model, index):
        if editor.hasAcceptableInput():
            model.setData(index, QVariant(editor.text()))

    def updateEditorGeometry(self, editor, option, index):
        rect = option.rect
        # ensure that the frame doesn't conceal any of the text
        rect.setTop(rect.top()-2)
        rect.setBottom(rect.bottom()+2)
        rect.setLeft(rect.left()-1)
        editor.setGeometry(rect)




class PacketView(QTreeView):
    dump_packet = pyqtSignal(object)

    def __init__(self, parent = None):
        QTreeView.__init__(self, parent)
        self.dump_selected_act = QAction("Dump selected", self)
        self.dump_selected_act.triggered.connect(self.dump_selected)
        self.remove_selected_act = QAction("Remove selected", self)
        self.remove_selected_act.triggered.connect(self.remove_selected)
        self.remove_selected_act.setShortcut(QKeySequence.Delete)
        self.addAction(self.remove_selected_act)
        self.remove_all_act = QAction("Remove all", self)
        self.remove_all_act.triggered.connect(self.remove_all)
        self.passthru_toggle = QAction("Passthrough", self)
        self.passthru_toggle.setCheckable(True)
        self.passthru_toggle.setChecked(True)
        self.autoscroll_toggle = QAction("Autoscroll", self)
        self.autoscroll_toggle.setCheckable(True)
        self.autoscroll_toggle.setChecked(False)
        self.pause_toggle = QAction("Pause capture", self)
        self.pause_toggle.setCheckable(True)
        self.pause_toggle.setChecked(False)
        self.delegate = HexEditDelegate()
        self.setItemDelegateForColumn(DATA_COL, self.delegate)
        self.autoscroll_timer = QTimer(self)
        self.autoscroll_timer.setSingleShot(True)
        self.autoscroll_timer.timeout.connect(self.scrollToBottom)

    def contextMenuEvent(self, event):
        menu = QMenu()
        menu.addAction(self.dump_selected_act)
        menu.addSeparator()
        menu.addAction(self.remove_selected_act)
        menu.addAction(self.remove_all_act)
        menu.addSeparator()
        menu.addAction(self.autoscroll_toggle)
        menu.addAction(self.passthru_toggle)
        menu.addSeparator()
        menu.addAction(self.pause_toggle)
        menu.exec_(event.globalPos())

    def remove_selected(self):
        rows = self.selectionModel().selectedRows()
        rows = map(lambda x: QPersistentModelIndex(x), rows)
        for idx in rows:
            self.model().removeRow(idx.row())

    def remove_all(self):
        self.model().clear()

    def new_row(self, parent, start, end):
        if self.autoscroll_toggle.isChecked() and not self.autoscroll_timer.isActive():
            self.autoscroll_timer.start(50)

    def dump_selected(self):
        selected = self.selectionModel().selectedRows()
        self.passthru_toggle.setChecked(False)
        # sort by row - dump packets in the order they appear
        selected.sort(cmp=lambda x,y: cmp(x.row(), y.row()))
        for idx in selected:
            packet = self.model().data(idx, 32).toPyObject()
            self.dump_packet.emit(packet)
        
        



class FilterWidget(QWidget):
    new_view_filter = pyqtSignal(str)
    new_cap_filter = pyqtSignal(str)

    def __init__(self, parent = None):
        QWidget.__init__(self, parent)
        self.view_filter_edit = QLineEdit()
        self.view_filter_edit.setPlaceholderText("Display filter")
        self.view_filter_clear = QPushButton(QIcon.fromTheme("editclear"), "")
        self.cap_filter_edit = QLineEdit()
        self.cap_filter_edit.setPlaceholderText("Capture filter")
        self.cap_filter_clear = QPushButton(QIcon.fromTheme("editclear"), "")

        self.hb = QHBoxLayout()
        self.hb.addWidget(self.view_filter_edit)
        self.hb.addWidget(self.view_filter_clear)
        self.hb.addWidget(self.cap_filter_edit)
        self.hb.addWidget(self.cap_filter_clear)
        self.setLayout(self.hb)

        self.view_filter_clear.clicked.connect(self.clear_view_filter)
        self.cap_filter_clear.clicked.connect(self.clear_cap_filter)
        self.view_filter_edit.returnPressed.connect(self.update_view_filter)
        self.cap_filter_edit.returnPressed.connect(self.update_cap_filter)
        
    def update_view_filter(self):
        #TODO validation
        self.new_view_filter.emit(str(self.view_filter_edit.text()))

    def clear_view_filter(self):
        self.view_filter_edit.setText("")
        self.update_view_filter()

    def update_cap_filter(self):
        #TODO validation
        self.new_cap_filter.emit(str(self.cap_filter_edit.text()))

    def clear_cap_filter(self):
        self.cap_filter_edit.setText("")
        self.update_cap_filter()



class USBView(QApplication):
    def __init__(self, argv):
        QApplication.__init__(self, argv)
        self.w = QWidget()
        self.w.resize(800, 600)

        self.packetmodel = PacketModel()
        self.proxy = PacketFilterProxyModel()
        self.proxy.setSourceModel(self.packetmodel)
        self.packetview = PacketView()
        self.packetview.setRootIsDecorated(False)
        self.packetview.setModel(self.proxy)
        self.packetview.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.packetview.setUniformRowHeights(True)
        self.packetview.dump_packet.connect(self.dump_packet)
        self.proxy.rowsInserted.connect(self.packetview.new_row)
        self.packetview.passthru_toggle.toggled.connect(self.passthru_toggled)
        self.packetview.pause_toggle.toggled.connect(self.pause_toggled)

        self.filterpane = FilterWidget()
        self.filterpane.new_view_filter.connect(self.proxy.set_filter)
        self.filterpane.new_cap_filter.connect(self.new_cap_filter)

        self.vb = QVBoxLayout()
        self.vb.addWidget(self.filterpane)
        self.vb.addWidget(self.packetview)
        self.w.setLayout(self.vb)
        self.w.show()

        self.pcapthread = PcapThread()
        self.pause_toggled(False)
        self.pcapthread.dump_opened.connect(self.dump_opened)
        self.pcapthread.start()

        self.dumper = None
        self.passthru = True
        self.filterexpr = None
	
    def dump_opened(self, dumper):
        self.dumper = dumper

    def passthru_toggled(self, state):
        self.passthru = state

    def pause_toggled(self, state):
        if state:
            self.pcapthread.new_packet.disconnect(self.new_packet)
        else:
            self.pcapthread.new_packet.connect(self.new_packet)
    
    def new_packet(self, packet):
        if self.filterexpr:
            try:
                if not eval(self.filterexpr, packet):
                    return
            except Exception:
                return

        if self.passthru:
            self.dump_packet(packet)
        self.packetmodel.new_packet(packet)

    def new_cap_filter(self, e):
        self.filterexpr = str(e)

    def dump_packet(self, pack):
        if self.dumper is not None:
            try:
                self.dumper.dump(pack.hdr, pack.repack())
                sys.stdout.flush()
            except Exception:
                self.dumper = None



app = USBView(sys.argv)
sys.exit(app.exec_())

