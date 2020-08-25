from .utils import *
from .tasks import BaseTask
import threading

import nidaqmx
from nidaqmx.stream_writers import AnalogMultiChannelWriter
from nidaqmx.stream_readers import AnalogMultiChannelReader
from nidaqmx.stream_writers import DigitalMultiChannelWriter


class IOTaskNidaq(BaseTask):
    # This is only nidaq for now.
    def __init__(self,channels,modes):
        '''
        IOTask for using nidaqmx cards on Windows.
        '''
        super(IOTaskNidaq,self).__init__(channels,modes)
        self.buff_dtype = np.float64        
        
    def _create_tasks(self):
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
                self.task_do.do_channels.add_do_chan(
                    chanstr,
                    line_grouping = nidaqmx.constants.LineGrouping.CHAN_FOR_ALL_LINES)
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
        self.nsamples = int(np.max([np.max(s.shape)
                                    for s in stim if not s is None]))
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
            stims = np.zeros((self.n_output_chan,
                              self.nsamples),dtype = np.float64)
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

        self.run_do = False
        if not digstim is None:
            if not self.task_do is None:
                self.task_do.timing.cfg_samp_clk_timing(
                    rate = self.srate,
                    source = self.samp_clk_terminal,
                    active_edge=nidaqmx.constants.Edge.RISING,
                    samps_per_chan = self.nsamples)
                #this works for 32 bit ports only, all iputs must be on the same port for now.
                digstims = np.zeros((self.nsamples,32),dtype = np.uint32)
                for i in range(len(digstim)):
                    if digstim[i] is None:
                        continue
                    if not len(digstim[i]):
                        continue
                    digstims[:,i] = (digstim[i] > 0)
                self.di_writer = DigitalMultiChannelWriter(self.task_do.out_stream)
                self.di_writer.write_many_sample_port_uint32(np.packbits(
                    digstims,
                    bitorder='little').reshape((1,-1)).view(np.uint32))
                self.run_do = True
        self.acquired = False

    def _run(self, blocking = True):
        #self.task_ao.ao_channels.all.ao_dac_ref_allow_conn_to_gnd = True
        if not self.task_ai is None:
            self.task_ai.start()
        if self.run_do:
            self.task_do.start()
        if not self.task_ao is None:
            self.task_ao.start()
        if not self.task_clock is None:
            self.task_clock.start()
        #self.task_ao.ao_channels.all.ao_dac_ref_conn_to_gnd = False
        if blocking:
            self.reader.read_many_sample(
                self.data,
                number_of_samples_per_channel = self.nsamples,
                timeout = self.nsamples/self.srate + 1)
            self.data = self.data*aiconversion
            self.ibuff = self.nsamples
            self._clean_run()
            return self.data
        else:
            def run_thread():
                self.reader.read_all_avail_samp = True
                buffer = np.zeros((self.n_input_chan,1000),
                                  dtype=np.float64)
                while not self.ibuff == self.nsamples:
                    nsamples = self.reader.read_many_sample(
                        buffer,
                        number_of_samples_per_channel = 1000,
                        timeout = 1)
                    self.data[:,self.ibuff:self.ibuff+nsamples] = buffer[:,:nsamples]*aiconversion
                    self.ibuff += int(nsamples)
                self._clean_run()
            
            self.thread_task = threading.Thread(target=run_thread)
            self.thread_task.start()
            return None

    def _clean_run(self):
        self.task_clock.wait_until_done()
        self.task_clock.stop()
        
        if not self.task_ai is None:
            self.task_ai.wait_until_done()
            self.task_ai.stop()
        if not self.task_ao is None:
            self.task_ao.wait_until_done()
            self.task_ao.stop()
        if self.run_do:
            self.task_do.wait_until_done()
            self.task_do.stop()
        self.acquired = True
        
    def _get_axon200B_mode(self):
        mm = int(np.round(self.task_axon200B_mode.read()))
        if mm in [2,1]:
            self.mode = 'cc'
        elif mm == 3:
            self.mode = 'cc=0'
        elif mm in [4,6]:
            self.mode = 'vc'

        
    def close(self):
        self.task_ai.close()
        self.task_ao.close()
        self.task_do.close()
        self.task_clock.close()
