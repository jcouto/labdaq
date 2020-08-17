from .utils import *
import nidaqmx
from nidaqmx.stream_writers import AnalogMultiChannelWriter
from nidaqmx.stream_readers import AnalogMultiChannelReader

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
        self.digioutput_chan_index = np.where(chantypes == 'digital_output')[0]
        self.input_chan_index = np.where(chantypes == 'analog_input')[0]
        self.n_output_chan = len(self.output_chan_index)
        self.n_digioutput_chan = len(self.digioutput_chan_index)
        self.n_input_chan = len(self.input_chan_index)
        # Check of there is a special channel type: 'axon200B_mode'
        self.axon200B_mode = np.where(chantypes == 'axon200B_mode')[0]
        
        
    def _create_tasks(self):
        self.task_ai = None
        self.task_ao = None
        self.task_do = None
        self.task_ao_modes = []
        self.task_do_modes = []
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
        if len(self.digioutput_chan_index):
            for ichan in self.digioutput_chan_index:
                dev = self.chaninfo[ichan]['device']
                if 'ni:' in dev:
                    dev = dev.strip('ni:')
                    chanstr = dev+'/'+self.chaninfo[ichan]['channel']
                    if self.task_do is None:
                        self.task_do = nidaqmx.Task()
                    self.task_do.do_channels.add_do_chan(chanstr)
                    self.task_do_modes.append(self.chaninfo[ichan]['modes'][0])
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
        # uses the device of the first channel.
        # this part needs to be better specified to make it more general.
        dev = self.chaninfo[0]['device']
        if 'ni:' in dev:
            dev = dev.strip('ni:')
        self.task_clock = nidaqmx.Task()
        self.task_clock.co_channels.add_co_pulse_chan_freq(
            dev + '/ctr0',freq = self.srate)
        self.samp_clk_terminal = '/{0}/Ctr0InternalOutput'.format(dev)
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

    def load(self,stim,digstim = None,use_ao_trigger=False):
        # check if the modes are up to date
        assert type(stim) is list, 'Stim needs to be a list of numpy arrays'
        self._check_modes()
        self.nsamples = np.max([np.max(s.shape) for s in stim if not s is None])
        aoconversion = self._get_conversion(False)
            
        if not self.task_ai is None and self.task_ao is None:
            self.task_ai.timing.cfg_samp_clk_timing(
                rate = self.srate,
                samps_per_chan = self.nsamples)
                
        if not self.task_ao is None:
            self.task_ao.timing.cfg_samp_clk_timing(rate = self.srate,
                                                    samps_per_chan = self.nsamples)
            self.task_ao.export_signals.export_signal(nidaqmx.constants.Signal.SAMPLE_CLOCK, 'PFI0')
            if not self.task_ai is None:
                if use_ao_trigger:
                    self.task_ai.triggers.start_trigger.cfg_dig_edge_start_trig('ao/StartTrigger')

                    self.task_ai.timing.cfg_samp_clk_timing(rate = self.srate,
                                                            source = 'PFI0',
                                                            samps_per_chan = self.nsamples)

            # Take care of the conversions
            stims = np.zeros((self.n_output_chan,self.nsamples),dtype = np.float64)
            # Fix the analog output conversions
            for i in range(self.n_output_chan):
                if i < len(stim):
                    if stim[i] is None:
                        continue
                    if not len(stim[i]):
                        continue
                    stims[i] = stim[i]*aoconversion[i]

            if hasattr(self,'task_clock'):
                self.task_clock.timing.cfg_implicit_timing(
                    samps_per_chan=self.nsamples)
                
                if not self.task_ao is None:
                    self.task_ao.timing.cfg_samp_clk_timing(
                        self.srate,
                        source=self.samp_clk_terminal,
                        active_edge=nidaqmx.constants.Edge.RISING,
                        samps_per_chan=self.nsamples)
                if not self.task_ai is None:
                    self.task_ai.timing.cfg_samp_clk_timing(
                        self.srate,
                        source=self.samp_clk_terminal,
                        active_edge=nidaqmx.constants.Edge.FALLING,
                        samps_per_chan=self.nsamples)

            self.writer = AnalogMultiChannelWriter(self.task_ao.out_stream)
            self.reader = AnalogMultiChannelReader(self.task_ai.in_stream)
            self.writer.write_many_sample(stims)
            #self.task_ao.write(stims, auto_start=False)
        if not digstim is None:
            if not self.task_do is None:
                self.task_do.timing.cfg_samp_clk_timing(
                    rate = self.srate,
                    source = self.samp_clk_terminal,
                    active_edge=nidaqmx.constants.Edge.RISING,
                    samps_per_chan = self.nsamples)
                #self.task_do.triggers.start_trigger.cfg_dig_edge_start_trig('PFI0')

            digstims = np.zeros((self.n_digioutput_chan,self.nsamples),dtype = bool)
            for i in range(self.n_digioutput_chan):
                if i < len(digstim):
                    if digstim[i] is None:
                        continue
                    if not len(digstim[i]):
                        continue
                    digstims[i] = digstim[i]
            self.task_do.write(digstim[0]!=1, auto_start=False)
    def _check_modes(self):
        if not hasattr(self,'task_axon200B_mode'):
            self.mode = None
        mm = int(np.round(self.task_axon200B_mode.read()))
        if mm in [2,1]:
            self.mode = 'cc'
        elif mm == 3:
            self.mode = 'cc=0'
        elif mm in [4,6]:
            self.mode = 'vc'
        else:
            self.mode = None
        # update mode for each ai or ao
        if not self.mode is None:
            for i,ichan in enumerate(self.output_chan_index):
                modes = self.chaninfo[ichan]['modes']
                for m in modes: 
                    if m in self.mode:
                        self.task_ao_modes[i] = m
            for i,ichan in enumerate(self.input_chan_index):
                modes = self.chaninfo[ichan]['modes']
                for m in modes: 
                    if m in self.mode:
                        self.task_ai_modes[i] = m
        
    def run(self,blocking = True):
        self._check_modes()
        aiconversion = self._get_conversion(True)
        #self.task_ao.ao_channels.all.ao_dac_ref_allow_conn_to_gnd = True

        self.task_ai.start()
        if not self.task_do is None:
            self.task_do.start()
        if not self.task_ao is None:
            self.task_ao.start()
        if not self.task_clock is None:
            self.task_clock.start()

        #self.task_ao.ao_channels.all.ao_dac_ref_conn_to_gnd = False

        if blocking:
            self.data = np.zeros((self.n_input_chan,self.nsamples),dtype=np.float64)
            self.reader.read_many_sample(self.data,
                                         number_of_samples_per_channel = self.nsamples,
                                         timeout = self.nsamples/self.srate + 1)

            self.task_clock.wait_until_done()
            self.task_clock.stop()

            if not self.task_ai is None:
                self.task_ai.wait_until_done()
                self.task_ai.stop()
            if not self.task_ao is None:
                self.task_ao.wait_until_done()
                self.task_ao.stop()
            if not self.task_do is None:
                self.task_do.wait_until_done()
                self.task_do.stop()

            return np.array(self.data)*aiconversion
        else:
            return None

    def _get_conversion(self,get_ai = False):
        if get_ai:
            return np.array([self.modeinfo[m]['input_conversion'] for m in self.task_ai_modes])
        else:
            return np.array([self.modeinfo[m]['output_conversion'] for m in self.task_ao_modes])
        
    def close(self):
        self.task_ai.close()
        self.task_ao.close()
