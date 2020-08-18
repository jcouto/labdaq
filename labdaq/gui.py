from PyQt5.QtWidgets import (QApplication,
                             QWidget,
                             QMainWindow,
                             QDockWidget,
                             QFormLayout,
                             QHBoxLayout,
                             QGridLayout,
                             QVBoxLayout,
                             QPushButton,
                             QGridLayout,
                             QTreeWidgetItem,
                             QTreeView,
                             QTextEdit,
                             QLineEdit,
                             QCheckBox,
                             QComboBox,
                             QSlider,
                             QListWidget,
                             QLabel,
                             QProgressBar,
                             QFileDialog,
                             QMessageBox,
                             QDesktopWidget,
                             QListWidgetItem,
                             QFileSystemModel,
                             QAbstractItemView,
                             QMenu, QAction)

from PyQt5 import QtCore
from PyQt5.QtGui import QStandardItem, QStandardItemModel,QColor
from PyQt5.QtCore import Qt, QTimer,QMimeData
import pyqtgraph as pg

from .utils import *
from .stimgen import *

class SealTestWidget(QWidget):
    def __init__(self,task,interval = 500, amplitude = [10,200],duration=0.010):
        super(SealTestWidget,self).__init__()
        self.lay = QGridLayout()
        self.setLayout(self.lay)
        self.plotw = pg.PlotWidget()
        self.plots = []
        self.lay.addWidget(self.plotw,0,1,1,1)
        self.task = task
        self.srate = self.task.srate
        self.amplitude = 0
        self.duration = duration
        self.amplitudes = amplitude

        self._init_gui()
        self.set_amp()
        self.task.load([self.get_pulse()])
        data = self.task.run()
        if len(data.shape) > 1:
            for x in data:
                self.plots.append(self.plotw.plot(np.arange(len(x))/self.srate,x))
        else:
            self.plots.append(self.plotw.plot(np.arange(len(data))/self.srate,data))

    def _init_gui(self):
        w = QWidget()
        l = QFormLayout()
        w.setLayout(l)
        self.startstopw = QCheckBox()
        self.startstopw.setChecked(True)
        l.addRow('seal test',self.startstopw)
        self.offsetw = QLabel('{0} mV')
        l.addRow('baseline',self.offsetw)
        self.modew = QLabel('?')
        l.addRow('mode',self.modew)
        self.resw = QLabel('?')
        l.addRow('resistance',self.resw)
        self.ccoffset = 0
        self.vcoffset = 0
        self.ccoffsetw = QSlider()
        self.ccoffsetw.setMaximum(500)
        self.ccoffsetw.setMinimum(-500)
        labelcc = QLabel('CC offset [0 pA]')
        self.R = 0
        def ccchange(value):
            self.ccoffset = value
            labelcc.setText('CC offset [<b>{0} pA</b>]'.format(value))
        self.ccoffsetw.valueChanged.connect(ccchange)
        self.ccoffsetw.setValue(self.ccoffset)
        l.addRow(labelcc,self.ccoffsetw)
        self.vcoffsetw = QSlider()
        self.vcoffsetw.setMaximum(120)
        self.vcoffsetw.setMinimum(-120)
        labelvc = QLabel('VC offset [0 mV]')
        l.addRow(labelvc,self.vcoffsetw)
        def vcchange(value):
            self.vcoffset = value
            labelvc.setText('VC offset [<b>{0} mV</b>]'.format(value))
        self.vcoffsetw.valueChanged.connect(vcchange)
        self.vcoffsetw.setValue(self.vcoffset)

        self.zerooffsetsw = QPushButton('zero offsets')
        l.addRow(self.zerooffsetsw)
        def zero(value):
            self.vcoffsetw.setValue(0)
            self.ccoffsetw.setValue(0)
        self.zerooffsetsw.clicked.connect(zero)
        self.lay.addWidget(w,0,0,1,1)
        self.timer = QTimer()
        self.timer.timeout.connect(self._update)
        self.timer.start(1000.*(self.duration*3))
        self.startstopw.stateChanged.connect(self.start_stop)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Left:
            if not self.task.mode is None:
                if self.task.mode == 'vc':
                    self.vcoffsetw.setValue(self.vcoffset-10)
                else:
                    self.ccoffsetw.setValue(self.ccoffset-25)
        elif event.key() == QtCore.Qt.Key_Right:
            if not self.task.mode is None:
                if self.task.mode == 'vc':
                    self.vcoffsetw.setValue(self.vcoffset+10)
                else:
                    self.ccoffsetw.setValue(self.ccoffset+25)
        elif event.key() == 2:
            state = self.startstopw.isChecked()
            self.startstopw.setChecked(not state)
        #else:
        #    print(event.key())
        event.accept()

        
    def start_stop(self):
        if self.startstopw.isChecked():
            self.timer.start(1000.*(self.duration*3))
        else:
            self.timer.stop()
            
    def set_amp(self):
        if self.task.mode is None:
            self.amplitude = 0
        else:
            if self.task.mode == 'vc':
                self.amplitude = self.amplitudes[0]
            else:
                self.amplitude = self.amplitudes[1]
            
    def get_pulse(self):
        offset = 0
        if not  self.task.mode is None:
            if self.task.mode == 'vc':
                offset = float(self.vcoffsetw.value())
            elif self.task.mode == 'cc':
                offset = float(self.ccoffsetw.value())

        pulse = [[self.duration,1,0,0,0,0,0,0,0,0],
                [self.duration,1,self.amplitude,0,0,0,0,0,0,0],
                [self.duration,1,0,0,0,0,0,0,0,0]]
        
        return stimgen_waveform(pulse,srate = self.task.srate)+offset
    def closeEvent(self,event):
        self.timer.stop()
        self.task.close()
        event.accept()
        
    def _update(self):
        self.set_amp()
        self.task.load([self.get_pulse()])
        data = self.task.run().astype(np.float32)
        
        offset = np.nanmean(data[0,:int(0.7*self.duration*self.srate)])
        post = np.nanmean(data[0,int(1.1*self.duration*self.srate):int(
            1.9*self.duration*self.srate)])
        if not self.task.mode is None:
            if self.task.mode == 'vc':
                R = (self.amplitude*1e-3/((post-offset)*1e-12))/1e6  
                self.modew.setText('<b> {0} </b>'.format('voltage clamp'))
                self.offsetw.setText('{0:.2f} pA'.format(offset))
            else:
                R = (self.amplitude*1e-3/((post-offset)*1e-12))/1e10  
                self.offsetw.setText('{0:.2f} mV'.format(offset))
                self.modew.setText('<b> {0} </b>'.format('current clamp'))
            self.R = R #(R + self.R*29)/30.
            self.resw.setText('{0:.2f} MOhm'.format(self.R))
        if len(data.shape) > 1:
            for i,x in enumerate(data):
                self.plots[i].setData(x=np.arange(len(x))/self.srate,y = x)
        else:
            self.plots[0].setData(x=np.arange(len(data))/self.srate,y = data)


def main():
    from .nidaq import IOTask
    import sys
    pref = default_preferences
    task = IOTask(pref['channels'],pref['channel_modes'])

    app = QApplication(sys.argv)
    test = SealTestWidget(task)
    test.show()
    sys.exit(app.exec_())

    pass

