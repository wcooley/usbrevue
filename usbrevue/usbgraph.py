#!/usr/bin/env python
#
# Copyright (C) 2011 Austin Leirvik <aua at pdx.edu>
# Copyright (C) 2011 Wil Cooley <wcooley at pdx.edu>
# Copyright (C) 2011 Joanne McBride <jirab21@yahoo.com>
# Copyright (C) 2011 Danny Aley <danny.aley@gmail.com>
# Copyright (C) 2011 Erich Ulmer <blurrymadness@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import sys
from usbview import PcapThread
from usbrevue import Packet
from PyQt4 import Qt
from PyQt4.QtGui import *
from PyQt4.QtCore import QAbstractTableModel, QModelIndex, QVariant, QString, QByteArray, pyqtSignal, QTimer
import PyQt4.Qwt5 as Qwt
import numpy as np
import random
import re


class ByteModel(QAbstractTableModel):
    """Qt Model for byte data."""

    row_added = pyqtSignal() # emit when a new usb packet is received
    col_added = pyqtSignal() # emit when a new usb packet's data payload is larger than any we've seen before
    cb_checked = pyqtSignal(int) # emit when a column checkbox is checked
    cb_unchecked = pyqtSignal(int) # emit when a column checkbox is unchecked

    def __init__(self, parent=None):
        QAbstractTableModel.__init__(self, parent)

        # to keep track of which column checkboxes are checked
        self.cb_states = list()


    def rowCount(self, parent = QModelIndex()):
        if len(single_bytes) > 0:
            # all byte arrays will have the same length, so just get the lowest one, since if there are any bytes at all, then we've have that one
            return len(single_bytes[0])+1
        else:
            return 1

    def columnCount(self, parent = QModelIndex()):
        return len(single_bytes)

    def data(self, index, role = Qt.Qt.DisplayRole):
        row = index.row()
        col = index.column()
        if row != 0:
            val = single_bytes[col][row-1]

        if role == Qt.Qt.DisplayRole:
            if row == 0:
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
        if index.row() == 0:
            return Qt.Qt.ItemIsUserCheckable | Qt.Qt.ItemIsEnabled
        else:
            return Qt.Qt.ItemIsEnabled | Qt.Qt.ItemIsSelectable

    def new_packet(self, packet):
        if len(packet.data) > 0:
            if len(single_bytes) > 0:
                l = len(single_bytes[0])
            else:
                l = 0
            w = len(single_bytes)

            first_row = True if len(single_bytes) == 0 else False
            if len(packet.data) > len(single_bytes):
                self.beginInsertColumns(QModelIndex(), w, max(len(single_bytes), len(packet.data) - 1))
                for i in range(len(packet.data) - len(single_bytes)):
                    if first_row:
                        single_bytes.append(list())
                        self.cb_states.append(0)
                    else:
                        single_bytes.append([-1] * len(single_bytes[0]))
                        self.cb_states.append(0)
                self.endInsertColumns()
                self.col_added.emit()

            self.beginInsertRows(QModelIndex(), l, l)
            offset = 0
            for b in packet.data:
                single_bytes[offset].append(b)
                offset += 1
            while offset < len(single_bytes):
                single_bytes[offset].append(-1)
                offset += 1
            self.endInsertRows()
            self.row_added.emit()

            for cb in custom_bytes:
                cb_run = re.sub(r'\[(\d+)\]', r'single_bytes[\1][-1]', cb)

                composite_bytes = re.findall(r'single_bytes\[(\d+)\]', cb_run)

                if not -1 in [single_bytes[int(c)][-1] for c in composite_bytes]:
                    try:
                        custom_bytes[cb].append(eval(cb_run))
                    except SyntaxError:
                        #TODO: handle
                        pass
                else:
                    custom_bytes[cb].append(-1)
                    


class ByteView(QTableView):
    """Byte table view."""

    def __init__(self, parent=None):
        QTableView.__init__(self, parent)

        self.autoscroll_toggle = QAction("Autoscroll", self)
        self.autoscroll_toggle.setCheckable(True)
        self.autoscroll_toggle.setChecked(False)

        self.autoscroll_timer = QTimer(self)
        self.autoscroll_timer.setSingleShot(True)
        self.autoscroll_timer.timeout.connect(self.scrollToBottom)

    def contextMenuEvent(self, event):
        menu = QMenu()
        menu.addAction(self.autoscroll_toggle)
        menu.exec_(event.globalPos())

    def col_added(self):
        self.resizeColumnsToContents()

    def row_added(self):
        if self.autoscroll_toggle.isChecked() and not self.autoscroll_timer.isActive():
            self.autoscroll_timer.start(50)

# Acceptable colors to plot with
colors = [(0,255,255),
          (0,0,0),
          (0,0,255),
          (138,43,226),
          (165,42,42),
          (95,158,160),
          (127,255,0),
          (210,105,30),
          (255,127,80),
          (100,149,237),
          (0,255,255),
          (0,0,139),
          (0,139,139),
          (184,134,11),
          (0,100,0),
          (189,183,107),
          (139,9,139),
          (85,107,47),
          (255,140,0),
          (153,50,204),
          (139,0,0),
          (233,150,122),
          (143,188,143),
          (72,61,139),
          (47,79,79),
          (0,206,209),
          (148,0,211),
          (255,20,147),
          (178,34,34),
          (34,139,34),
          (218,165,32)]


class BytePlot(Qwt.QwtPlot):
    """Plot of selected byte values"""

    def __init__(self, *args):
        Qwt.QwtPlot.__init__(self, *args)

        self.setCanvasBackground(Qt.Qt.white)
        self.alignScales()

        self.x_range = 200

        random.seed()

        self.curves = {}
        self.custom_curves = {}

        self.insertLegend(Qwt.QwtLegend(), Qwt.QwtPlot.BottomLegend)

    def alignScales(self):
        self.canvas().setFrameStyle(Qt.QFrame.Box | Qt.QFrame.Plain)
        self.canvas().setLineWidth(1)
        self.setAxisScaleDraw(0, ByteScale())
        for i in range(Qwt.QwtPlot.axisCnt):
            scaleWidget = self.axisWidget(i)
            if scaleWidget:
                scaleWidget.setMargin(0)
            scaleDraw = self.axisScaleDraw(i)
            if scaleDraw:
                scaleDraw.enableComponent(Qwt.QwtAbstractScaleDraw.Backbone, False)
        self.setAxisTitle(0, "Byte value")
        self.setAxisTitle(2, "Packet sequence number")

    def row_added(self):
        l = len(single_bytes[0])
        for c in self.curves:
            mask = [j >= 0 for j in single_bytes[c]]
            self.set_curve_data(l, self.curves[c], range(l), single_bytes[c], mask)
        for c in self.custom_curves:
            mask = [j >= 0 for j in custom_bytes[c]]
            self.set_curve_data(l, self.custom_curves[c], range(l), custom_bytes[c], mask)

        self.replot()

    def cb_checked(self, column):
        if column not in self.curves:
            l = len(single_bytes[0])
            mask = [j >= 0 for j in single_bytes[column]]
            self.curves[column]= ByteCurve("Byte " + str(column))
            self.set_curve_data(l, self.curves[column], range(l), single_bytes[column], mask)

        r, g, b = colors.pop(random.randint(0, len(colors)-1))
        color = QColor(r, g, b)
        self.curves[column].setPen(QPen(QBrush(color), 2))
        self.curves[column].setStyle(Qwt.QwtPlotCurve.Dots)

        self.curves[column].attach(self)

        self.replot()

    def cb_unchecked(self, column):
        self.curves[column].detach()
        colors.append(self.curves[column].pen().brush().color().getRgb()[:-1])

        self.replot()

    def new_custom_bytes(self, string):
        byte_def_strings = [str(s).strip() for s in re.split(',', string)]
        to_remove = list()
        for cc in self.custom_curves:
            if cc not in byte_def_strings:
                to_remove.append(cc)
                self.custom_curves[cc].detach()
                colors.append(self.custom_curves[cc].pen().brush().color().getRgb()[:-1])
                del custom_bytes[cc]

        for cc in to_remove:
            del self.custom_curves[cc]

        for d in byte_def_strings:
            if not len(d) == 0:
                d_run = re.sub(r'\[(\d+)\]', r'single_bytes[\1][pos]', d)

                # find out what byte values are being used
                composite_bytes = re.findall(r'single_bytes\[(\d+)\]', d_run)

                if d not in self.custom_curves:
                    self.custom_curves[d] = ByteCurve(d)
                    custom_bytes[d] = list()
                    self.custom_curves[d].attach(self)
                    for pos in range(len(single_bytes[0])):
                        if not -1 in [single_bytes[int(c)][pos] for c in composite_bytes]:
                            try:
                                custom_bytes[d].append(eval(d_run))
                            except SyntaxError:
                                #TODO: handle
                                pass
                        else:
                            custom_bytes[d].append(-1)
                else:
                    for pos in range(len(custom_bytes[d]), len(single_bytes[0])):
                        if not -1 in [single_bytes[int(c)][pos] for c in composite_bytes]:
                            custom_bytes[d].append(eval(d_run))
                        else:
                            custom_bytes[d].append(-1)

                mask = [j >= 0 for j in custom_bytes[d]]
                self.set_curve_data(len(single_bytes[0]), self.custom_curves[d], range(len(single_bytes[0])), custom_bytes[d], mask)

                r, g, b = colors.pop(random.randint(0, len(colors)-1))
                color = QColor(r, g, b)
                self.custom_curves[d].setPen(QPen(QBrush(color), 2))
                self.custom_curves[d].setStyle(Qwt.QwtPlotCurve.Dots)

        self.replot()

    def set_curve_data(self, length, curve, x, y, mask):
        if length > self.x_range:
            curve.setData(ByteData(x[length-self.x_range:length], y[length-self.x_range:length], mask[length-self.x_range:length]))
            self.setAxisScale(2, length-self.x_range, length)
        else:
            print len(x), len(y)
            curve.setData(ByteData(x[:min(length, self.x_range)], y[:min(length, self.x_range)], mask[:min(length, self.x_range)]))
                        
    def change_x_range(self, range):
        self.x_range = range

        self.row_added()

    def clamp_axis(self, min, max):
        if min >= 0 and max >= 0:
            self.setAxisScale(0, min, max)
        else:
            self.setAxisAutoScale(0)

        self.replot()


class ByteScale(Qwt.QwtScaleDraw):
    """Subclassed QwtScaleDraw so that y-axis labeled are displayed as hex"""

    def __init__(self):
        Qwt.QwtScaleDraw.__init__(self)

    def label(self, value):
        return Qwt.QwtText('%X' % value)


class ByteData(Qwt.QwtArrayData):
    """Subclassed QwtArrayData with mask"""

    def __init__(self, x, y, mask):
        Qwt.QwtArrayData.__init__(self, x, y)
        self.__mask = np.asarray(mask, bool)
        self.__x = np.asarray(x)
        self.__y = np.asarray(y)

    def copy(self):
        return self

    def mask(self):
        return self.__mask


class ByteCurve(Qwt.QwtPlotCurve):
    """Subclassed QwtPlotCurve so that data is masked"""

    def __init__(self, title=None):
        Qwt.QwtPlotCurve.__init__(self, title)

    def draw(self, painter, xMap, yMap, rect):
        try:
            indices = np.arange(self.data().size())[self.data().mask()]
            if len(indices > 0):
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


class ByteValWidget(QWidget):
    """Input area for the user to specify custom byte values."""

    byte_vals_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.y_axis_label = QLabel("y = ")
        self.y_axis_edit = QLineEdit()

        self.hb = QHBoxLayout()
        self.hb.addWidget(self.y_axis_label)
        self.hb.addWidget(self.y_axis_edit)
        self.setLayout(self.hb)

        self.y_axis_edit.returnPressed.connect(self.update_byte_vals)

    def update_byte_vals(self):
        self.byte_vals_changed.emit(str(self.y_axis_edit.text()))


class ClampYAxisWidget(QGroupBox):
    """Let the user specify max and min values for the y-axis."""

    y_axis_vals_changed = pyqtSignal(int, int)

    def __init__(self, title, parent=None):
        QGroupBox.__init__(self, title, parent)

        self.y_clamp_group_layout = QHBoxLayout()
        self.y_clamp_group_layout.addWidget(QLabel('Minimum:'))
        self.y_min = QLineEdit()
        self.y_clamp_group_layout.addWidget(self.y_min)
        self.y_clamp_group_layout.addWidget(QLabel('Maximum:'))
        self.y_max = QLineEdit()
        self.y_clamp_group_layout.addWidget(self.y_max)
        self.y_clamp_button = QPushButton('Apply')
        self.y_clamp_button.clicked.connect(self.clicked)
        self.y_clamp_group_layout.addWidget(self.y_clamp_button)
        self.setLayout(self.y_clamp_group_layout)
        self.setMaximumHeight(100)
        self.resize(300, 100)

    def clicked(self):
        if not self.y_min.text() and not self.y_max.text():
            self.y_axis_vals_changed.emit(-1, -1)
        elif self.y_min.text() and self.y_max.text():
            min = int(str(self.y_min.text()), 0)
            max = int(str(self.y_max.text()), 0)

            self.y_axis_vals_changed.emit(min, max)
        else:
            msg = QMessageBox()
            msg.setText('Please specify a minimum and maximum value, or clear both to reset.')
            msg.exec_()


class PlotWindowSliderWidget(QGroupBox):
    """Let the user change the width of the plot window."""
    value_changed = pyqtSignal(int)

    def __init__(self, title, parent=None):
        QGroupBox.__init__(self, title, parent)

        self.plot_range = QSlider()
        self.plot_range.setOrientation(Qt.Qt.Horizontal)
        self.plot_range.setRange(10, 1000)
        self.plot_range.setValue(200)
        self.plot_range.setTickInterval(50)
        self.plot_range.setTickPosition(Qt.QSlider.TicksBelow)
        self.plot_range.valueChanged.connect(lambda val: self.value_changed.emit(val))
        self.plot_range_labels = QHBoxLayout()
        self.plot_range_labels.addWidget(QLabel('10'))
        self.plot_range_labels.addWidget(self.plot_range)
        self.plot_range_labels.addWidget(QLabel('1000'))
        self.setLayout(self.plot_range_labels)
        self.setMaximumHeight(100)


class USBGraph(QApplication):
    def __init__(self, argv):
        QApplication.__init__(self, argv)
        self.w = QWidget()
        self.w.resize(800, 600)

        self.bytemodel = ByteModel()
        self.byteview = ByteView()
        self.byteview.setModel(self.bytemodel)
        self.bytevalwidget = ByteValWidget()
        self.byteplot = BytePlot()

        self.bytevalgroup = QGroupBox('Custom Byte Expressions')
        self.groupvb = QVBoxLayout()
        self.groupvb.addWidget(self.bytevalwidget)
        self.bytevalgroup.setLayout(self.groupvb)
        self.bytevalgroup.setMaximumHeight(100)
        self.bytevalgroup.setMinimumWidth(400)

        self.x_range = PlotWindowSliderWidget('Plot Window')
        self.x_range.value_changed.connect(self.byteplot.change_x_range)

        self.y_clamp = ClampYAxisWidget('Clamp Y Axis')
        self.y_clamp.y_axis_vals_changed.connect(self.byteplot.clamp_axis)

        self.bytemodel.row_added.connect(self.byteplot.row_added)
        self.bytemodel.row_added.connect(self.byteview.row_added)
        self.bytemodel.col_added.connect(self.byteview.col_added)
        self.bytemodel.cb_checked.connect(self.byteplot.cb_checked)
        self.bytemodel.cb_unchecked.connect(self.byteplot.cb_unchecked)

        self.bytevalwidget.byte_vals_changed.connect(self.byteplot.new_custom_bytes)

        self.main_area = QSplitter()
        self.main_area.addWidget(self.byteview)
        self.main_area.addWidget(self.byteplot)
        self.main_area.setSizes([400,400])

        self.lower_right_area = QVBoxLayout()
        self.lower_right_area.addWidget(self.x_range)
        self.lower_right_area.addWidget(self.y_clamp)

        self.lower_area = QHBoxLayout()
        self.lower_area.addWidget(self.bytevalgroup)
        self.lower_area.addLayout(self.lower_right_area)

        self.vb = QVBoxLayout()
        self.vb.addWidget(self.main_area)
        self.vb.addItem(self.lower_area)
        
        self.w.setLayout(self.vb)
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


single_bytes = list()
custom_bytes = {}


if __name__ == "__main__":
    app = USBGraph(sys.argv)
    sys.exit(app.exec_())

