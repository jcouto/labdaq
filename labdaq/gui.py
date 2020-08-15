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
        lay = QGridLayout()
        self.setLayout(lay)
        self.plotw = pg.PlotWidget()
        self.plots = []
        lay.addWidget(self.plotw,0,1,1,1)
        self.task = task
        self.srate = self.task.srate
        self.amplitude = 0
        self.duration = duration
        self.amplitudes = amplitude

        self.set_amp()
        self.task.load([self.get_pulse()])
        data = self.task.run()
        if len(data.shape) > 1:
            for x in data:
                self.plots.append(self.plotw.plot(np.arange(len(x))/self.srate,x))
        else:
            self.plots.append(self.plotw.plot(np.arange(len(data))/self.srate,data))

        w = QWidget()
        l = QFormLayout()
        w.setLayout(l)
        self.startstopw = QCheckBox()
        self.startstopw.setChecked(True)
        l.addRow('Active',self.startstopw)
        lay.addWidget(w,0,0,1,1)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self._update)
        self.timer.start(1000.*(self.duration*3))
        self.startstopw.stateChanged.connect(self.start_stop)

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
        pulse = [[self.duration,1,0,0,0,0,0,0,0,0],
                [self.duration,1,self.amplitude,0,0,0,0,0,0,0],
                [self.duration,1,0,0,0,0,0,0,0,0]]
        
        return stimgen_waveform(pulse)
    def closeEvent(self,event):
        self.timer.stop()
        self.task.close()
        event.accept()
    def _update(self):
        self.set_amp()
        self.task.load([self.get_pulse()])
        data = self.task.run()
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

