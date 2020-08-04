import nidaqmx
import numpy as np

class IOTask():
    def __init__(self,channels):
        # init tasks
        self.task_ai = None
        self.task_ao = None
        self.task_di = None
        self.task_do = None
        self.srate = srate
        self.aoconversion = np.float32(aoconversion)
        self.aiconversion = np.float32(aiconversion)
        if not aichan is None:
            self.task_ai = nidaqmx.Task()
            self.task_ai.ai_channels.add_ai_voltage_chan(aichan)
            #elf.task_ai.triggers.sync_type.MASTER = True
            #elf.task_ai.control(nidaqmx.constants.TaskMode.TASK_COMMIT)
        if not aochan is None:
            self.task_ao = nidaqmx.Task()
            #f not self.task_ai is None:
            #   self.task_ao.triggers.sync_type.SLAVE = True
            self.task_ao.ao_channels.add_ao_voltage_chan(aochan)
        if not modechan is None:
            self.task_mode = nidaqmx.Task()
            self.task_mode.ai_channels.add_ai_voltage_chan(modechan)
        self.mode = None
        self._check_mode()
    def load(self,stim):
        self._check_mode()
        if self.mode in ['IC','IC=0']:
            aoconversion = self.aoconversion[1]
            print('in cclamp')
        else:
            aoconversion = self.aoconversion[0]
        self.nsamples = max(stim.shape)
        if not self.task_ai is None:
            self.task_ai.timing.cfg_samp_clk_timing(rate = self.srate,
                                                    samps_per_chan = self.nsamples)
        if not self.task_ao is None:
            self.task_ao.timing.cfg_samp_clk_timing(rate = self.srate,
                                                    samps_per_chan = self.nsamples)
            self.task_ao.write((stim*aoconversion).astype(np.float32), auto_start=False)
    
    def _check_mode(self):
        if not hasattr(self,'task_mode'):
            return None
        mm = int(np.round(self.task_mode.read()))
        if mm in [2,1,4]:
            self.mode = 'IC'
        elif mm == 3:
            self.mode = 'IC=0'
        elif mm in [4,5]:
            self.mode = 'VC'
        else:
            self.mode = None
    def run(self):
        self._check_mode()
        if self.mode in ['IC','IC=0']:
            aiconversion = self.aiconversion[1]
        else:
            aiconversion = self.aiconversion[0]
        self.task_ai.start()
        self.task_ao.start()
        data=self.task_ai.read(number_of_samples_per_channel = nidaqmx.constants. READ_ALL_AVAILABLE)
        self.task_ai.stop()
        self.task_ao.stop()
        return np.array(data)*aiconversion
    
    def close(self):
        self.task_ai.close()
        self.task_ao.close()
