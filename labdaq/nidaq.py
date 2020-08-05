import nidaqmx
import numpy as np


class IOTask():
    # This is only nidaq for now.
    def __init__(self,channels,modes):
        '''
        pref = default_preferences
        task = IOTask(channels, pref['channel_modes'])
        '''
        self.chaninfo = channels
        self.modeinfo = modes
        self.mode = None
        self._parse_channels()
        self._create_tasks()
        
    def _parse_channels(self):
        chantypes = np.array([c['type'] for c in self.chaninfo])
        self.output_chan_index = np.where(chantypes == 'analog_output')[0]
        self.input_chan_index = np.where(chantypes == 'analog_input')[0]
        self.n_output_chan = len(self.output_chan_index)
        self.n_input_chan = len(self.input_chan_index)
        # Check of there is a special channel type: 'axon200B_mode'
        self.axon200B_mode = np.where(chantypes == 'axon200B_mode')[0]
        
        
    def _create_tasks(self):
        self.task_ai = None
        self.task_ao = None
        self.task_ao_modes = []
        self.task_ai_modes = []
        if self.n_output_chan:
            for ichan in self.output_chan_index:
                dev = self.chaninfo[ichan]['device']
                if 'ni:' in dev:
                    dev = dev.strip('ni:')
                    chanstr = dev+'/'+self.chaninfo[ichan]['channel']
                    if self.task_ao is None:
                        self.task_ao = nidaqmx.Task()
                    if not 'range' in self.chaninfo[ichan].keys():
                        self.chaninfo[ichan]['range'] = [-10,10]
                    self.task_ao.ao_channels.add_ao_voltage_chan(
                        chanstr,
                        min_val = self.chaninfo[ichan]['range'][0],
                        max_val = self.chaninfo[ichan]['range'][1])
                    self.task_ao_modes.append(self.chaninfo[ichan]['modes'][0])
                    if 'acq_rate' in self.chaninfo[ichan].keys():
                        self.srate = self.chaninfo[ichan]['acq_rate']
        if self.n_input_chan:
            for ichan in self.input_chan_index:
                dev = self.chaninfo[ichan]['device']
                if 'ni:' in dev:
                    dev = dev.strip('ni:')
                    chanstr = dev+'/'+self.chaninfo[ichan]['channel']
                    if self.task_ai is None:
                        self.task_ai = nidaqmx.Task()
                    if not 'range' in self.chaninfo[ichan].keys():
                        self.chaninfo[ichan]['range'] = [-10,10]
                    self.task_ai.ai_channels.add_ai_voltage_chan(
                        chanstr,
                        min_val = self.chaninfo[ichan]['range'][0],
                        max_val = self.chaninfo[ichan]['range'][1])
                    self.task_ai_modes.append(self.chaninfo[ichan]['modes'][0])
                    if 'acq_rate' in self.chaninfo[ichan].keys():
                        self.srate = self.chaninfo[ichan]['acq_rate']
        # This should probably be on an independent function.
        if len(self.axon200B_mode):
            ichan = self.axon200B_mode[0]
            dev = self.chaninfo[ichan]['device']
            if 'ni:' in dev:
                dev = dev.strip('ni:')
                chanstr = dev+'/'+self.chaninfo[ichan]['channel']
                if not hasattr(self,'task_axon200B_mode'):
                    self.task_axon200B_mode = nidaqmx.Task()
                if not 'range' in self.chaninfo[ichan].keys():
                    self.chaninfo[ichan]['range'] = [-10,10]
                self.task_axon200B_mode.ai_channels.add_ai_voltage_chan(
                    chanstr,
                    min_val = self.chaninfo[ichan]['range'][0],
                    max_val = self.chaninfo[ichan]['range'][1])

    def load(self,stim,use_ao_trigger=False):
        # check if the modes are up to date
        self._check_modes()
        aoconversion = self._get_conversion(False)
        self.nsamples = max(stim.shape) # this is not very good
        if not self.task_ai is None:
            self.task_ai.timing.cfg_samp_clk_timing(
                rate = self.srate,
                samps_per_chan = self.nsamples)
        if use_ao_trigger:
            self.task_ai.triggers.start_trigger.cfg_dig_edge_start_trig('ao/StartTrigger')
        if not self.task_ao is None:
            self.task_ao.timing.cfg_samp_clk_timing(rate = self.srate,
                                                    samps_per_chan = self.nsamples)
            # Take care of the conversions
            self.task_ao.write((stim*aoconversion).astype(np.float32), auto_start=False)
    def _check_modes(self):
        if not hasattr(self,'task_axon200B_mode'):
            self.mode = None
        mm = int(np.round(self.task_axon200B_mode.read()))
        if mm in [2,1,4]:
            self.mode = 'cc'
        elif mm == 3:
            self.mode = 'cc=0'
        elif mm in [4,5]:
            self.mode = 'vc'
        else:
            self.mode = None
        # update mode for each ai or ao
        if not self.mode is None:
            for i,ichan in enumerate(self.self.output_chan_index):
                modes = self.chaninfo[ichan]['modes']
                for m in modes: 
                    if m in self.mode:
                        self.task_ao_modes[i] = m
            for i,ichan in enumerate(self.self.input_chan_index):
                modes = self.chaninfo[ichan]['modes']
                for m in modes: 
                    if m in self.mode:
                        self.task_ai_modes[i] = m
        
    def run(self,blocking = True):
        self._check_modes()
        aiconversion = self._get_conversion(True)
        self.task_ai.start()
        self.task_ao.start()
        if blocking:
            print(self.task_ai.timing.samp_clk_src)
            data = self.task_ai.read(number_of_samples_per_channel = nidaqmx.constants. READ_ALL_AVAILABLE)
            self.task_ao.wait_until_done()
            self.task_ai.wait_until_done()
            self.task_ai.stop()
            self.task_ao.stop()
            return np.array(data)*aiconversion
        else:
            return None

    def _get_conversion(self,get_ai = True):
        if get_ai:
            return np.array([self.modeinfo[m]['input_conversion'] for m in self.task_ai_modes])
        else:
            return np.array([self.modeinfo[m]['output_conversion'] for m in self.task_ao_modes])
        
    def close(self):
        self.task_ai.close()
        self.task_ao.close()
