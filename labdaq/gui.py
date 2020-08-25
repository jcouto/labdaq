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
from datetime import datetime
import socket

from .utils import *
from .stimgen import *
from .exputils import *

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
        data = self.task.run(blocking=True)
        if len(data.shape) > 1:
            for x in data:
                self.plots.append(self.plotw.plot(
                    np.arange(len(x))/self.srate,x))
        else:
            self.plots.append(self.plotw.plot(
                np.arange(len(data))/self.srate,data))

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

        pulse = [[self.duration,1,0],
                [self.duration,1,self.amplitude],
                [self.duration,1,0]]
        
        return stimgen_waveform(pulse,srate = self.task.srate)+offset
    def closeEvent(self,event):
        self.timer.stop()
        self.task.close()
        event.accept()
        
    def _update(self):
        self.set_amp()
        self.task.load([self.get_pulse()])
        data = self.task.run(blocking=True).astype(np.float32)
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
        else:
            self.modew.setText('<b> {0} </b>'.format('unknown'))
        if len(data.shape) > 1:
            for i,x in enumerate(data):
                self.plots[i].setData(x=np.arange(len(x))/self.srate,y = x)
        else:
            self.plots[0].setData(x=np.arange(len(data))/self.srate,y = data)


class ProtocolFileViewer(QTreeView):
     def __init__(self,folder,parent=None):
        super(ProtocolFileViewer,self).__init__()
        self.parent = parent
        self.fs_model = QFileSystemModel(self)
        self.fs_model.setReadOnly(True)
        self.setModel(self.fs_model)
        self.folder = folder
        self.setRootIndex(self.fs_model.setRootPath(folder))
        self.fs_model.removeColumn(1)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(3)
#         self.setDragEnabled(True)
#         self.setAcceptDrops(True)
#         self.setDragDropMode(QAbstractItemView.DragDrop)
#         self.setDropIndicatorShown(True)
#         #[self.hideColumn(i) for i in range(1,4)]
        self.setColumnWidth(0,self.width()*.3)
        def query_root(self):
            folder = QFileDialog().getExistingDirectory(self,"Select directory",os.path.curdir)
            self.setRootIndex(self.fs_model.setRootPath(folder))
            self.expandAll()
            self.folder = folder
            if hasattr(self.parent,'folder'):
                self.parent.folder.setText('{0}'.format(folder))

# A widget to run experiments
class ExpProtWidget(QWidget):
    def __init__(self,task,pref,protocolsfolder = None,parent = None):
        super(ExpProtWidget,self).__init__()
        self.parent = parent
        self.task = task
        self.pref = pref
        self.subject = 'exp_name'
        lay = QGridLayout()
        self.setLayout(lay)
        self.protocolsfolder = protocolsfolder
        self.fbrowse = ProtocolFileViewer(self.protocolsfolder)
        self.subjectw = QLineEdit()
        self.plotw = pg.PlotWidget()
        self.plots = []
        self.runbutton = QPushButton('Run exp prot')
        lay.addWidget(self.fbrowse,0,0,2,1)
        lay.addWidget(self.runbutton,2,0,1,1)
        lay.addWidget(self.subjectw,3,0,1,1)
        lay.addWidget(self.plotw,0,1,4,4)
        self.subjectw.setText(self.subject)
        self.runbutton.clicked.connect(self.run_file)
        
    def run_file(self):
        filenames = [self.fbrowse.fs_model.filePath(s)
                     for s in self.fbrowse.selectedIndexes()]
        fname = np.unique(filenames)[0]
        display('Selected {0}'.format(fname))
        if os.path.isdir(fname):
            display('This works only with ".expprot" files for now [{0}].'.format(fname))
            sys.stdout.flush()

            return
        if os.path.isfile(fname):
            if not os.path.splitext(fname)[1] == '.expprot':
                display('This works only with ".expprot" files for now [{0}].'.format(
                    os.path.splitext(fname)[1]))
                sys.stdout.flush()
                return
        # stop sealtest if it exists
        if hasattr(self.parent,'sealtest_widget'):
            self.parent.sealtest_widget.startstopw.setChecked(False)
            
        expfile = fname
        self.subject=self.subjectw.text()
        recorderpars = dict(self.pref['recorder'],subject = self.subject)

        expdict = parse_experiment_protocol(expfile)
        expdict,stim,digistim = parse_experiment(expdict,self.task)

        recorderpars['prot'] = os.path.basename(os.path.splitext(expfile)[0])
        # this will load and run
        if 'labcams' in expdict.keys():
            labcamsaddress = expdict['labcams'].split(':')
            labcamsaddress[-1] = int(labcamsaddress[-1])
            labcamsaddress = tuple(labcamsaddress)

            udplabcams = socket.socket(socket.AF_INET,
                                       socket.SOCK_DGRAM)
            udplabcams.sendto(b'softtrigger=0', labcamsaddress)
            time.sleep(0.01)
            udplabcams.sendto(b'manualsave=0', labcamsaddress)
            time.sleep(0.01)
        recorderpars['datetime'] = datetime.now().strftime("%Y%m%d_%H%M%S")
        for itrial in range(expdict['ntrials']):
            tstart = time.time()
            # get the filename
            filename = os.path.basename(
                self.pref['recorder']['path']) + '_{itrial}.{format}'
            recorderpars['filename'] = pjoin(recorderpars['path'], filename)
            recorderpars['itrial'] = itrial
            filename = recorderpars['filename'].format(**recorderpars)
            if 'labcams' in expdict.keys():
                udplabcams.sendto('expname={0}'.format(
                    os.path.basename(os.path.dirname(filename))).encode(
                        'utf-8'), labcamsaddress)    
                time.sleep(0.01)
                udplabcams.sendto(b'manualsave=1', labcamsaddress)
                time.sleep(0.01)
                udplabcams.sendto(b'softtrigger=1', labcamsaddress)
                time.sleep(0.01)
                udplabcams.sendto('log=trial:{0}'.format(
                    itrial).encode('utf-8'), labcamsaddress)
                time.sleep(0.01)
            self.task.load(stim = stim,digstim = digistim)
            # check if you need to load labcams
            sys.stdout.flush()
            self.task.run(blocking=False)
            taskdone = False
            while not self.task.acquired:
                taskdone = True
                QApplication.processEvents()
                dat = self.task.data[:,:self.task.ibuff]
                t = np.arange(dat.shape[1])/self.task.srate
                if not len(self.plots):
                    for d in dat:    
                        self.plots.append(self.plotw.plot(t,d))
                else:
                    for i,d in enumerate(dat):    
                        self.plots[i].setData(x=t,y = d)
                time.sleep(0.03)
            if taskdone:
                if 'labcams' in expdict.keys():
                    udplabcams.sendto(b'softtrigger=0', labcamsaddress)
                    time.sleep(0.1)
                    udplabcams.sendto(b'manualsave=0', labcamsaddress)
                # save
                h5_save(filename,self.task,self.pref,
                        stim=stim, digistim=digistim)
            if 'iti' in expdict.keys():
                tpassed = time.time() - tstart
                ttotal = expdict['duration'] - expdict['iti']
                if ( ttotal >= tpassed): 
                    time.sleep(ttotal - tpassed)
            sys.stdout.flush()
        if 'labcams' in expdict.keys():
            udplabcams.close()
    
def get_tree_path(items,root = ''):
    ''' Get the paths from a QTreeView item'''
    paths = []
    for item in items:
        level = 0
        index = item
        paths.append([index.data()])
        while index.parent().isValid():
            index = index.parent()
            level += 1
            paths[-1].append(index.data())
    for i,p in enumerate(paths):
        if None in p:
            paths[i] = ['']
    return ['/'.join(p[::-1]) for p in paths]

class LABDAQ_GUI(QMainWindow):
    app = None
    task = None
    def __init__(self,
                 task,
                 pref,
                 folder=None,
                 app=None):
        super(LABDAQ_GUI,self).__init__()
        self.setWindowTitle('labdaq')
        self.setDockOptions(QMainWindow.AllowTabbedDocks |
                            QMainWindow.AllowNestedDocks)
        self.task = task
        self.protfolder = folder
        self.pref = pref
        self.stimgen_widget = ExpProtWidget(self.task,
                                            self.pref,
                                            self.protfolder,
                                            parent = self)
        self.stimgen_tab = QDockWidget("stimulus",self)
        self.stimgen_tab.setWidget(self.stimgen_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.stimgen_tab)
        
        if 'cc' in self.task.modeinfo.keys():
            self.sealtest_widget = SealTestWidget(self.task)
            self.sealtest_tab = QDockWidget("seal test",self)
            self.sealtest_tab.setWidget(self.sealtest_widget)
            self.addDockWidget(Qt.LeftDockWidgetArea, self.sealtest_tab)

        self.show()
        

def main():
    
    from .tasks import IOTask
    import sys
    pref = get_preferences('default')
    protfolder = pjoin(os.path.expanduser('~'), 'labdaq/default/protocols')
    task = IOTask(pref['channels'],pref['channel_modes'])

    app = QApplication(sys.argv)
    gui = LABDAQ_GUI(task,pref,protfolder,app)
    gui.show()
    sys.exit(app.exec_())


    
def sealtest():
    from .nidaq import IOTask
    import sys
    pref = get_preferences()
    task = IOTask(pref['channels'],pref['channel_modes'])

    app = QApplication(sys.argv)
    test = SealTestWidget(task)
    test.show()
    sys.exit(app.exec_())


