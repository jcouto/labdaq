from .stimgen import *
from threading import Thread

class TriggeredOptogeneticsWaveform():
    def __init__(self,
                 device = 'dev1',
                 waveform_channel = 0,
                 trigger_channel = None,
                 sampling_rate = None,
                 vrange = 10):
        self.device = device
        self.waveform_channel = waveform_channel
        self.trigger_channel = trigger_channel
        self.vrange = vrange
        self.sampling_rate = sampling_rate
        import nidaqmx
        self.constants = nidaqmx.constants
        self.DaqError = nidaqmx.DaqError
        self.task_ao = nidaqmx.Task()
        self.task_ao.ao_channels.add_ao_voltage_chan('{0}/ao{1}'.format(self.device,self.waveform_channel),
                        min_val = -1*vrange,
                        max_val = vrange)
        from nidaqmx.stream_writers import AnalogMultiChannelWriter
        self.optosine_writer = AnalogMultiChannelWriter(
            self.task_ao.out_stream)

        if self.sampling_rate is None:
            self.sampling_rate = self.task_ao.timing.samp_clk_max_rate
        self.task_ao.timing.samp_clk_rate = self.sampling_rate
        self.waveform_parameters = None
        self.loaded = False
        self.trigger_task = False
        self.waveform = None
        
    def load_optosine(self,frequency = 1, amplitude = 1):
        self.task_ao.timing.samp_clk_rate = self.sampling_rate     
        self.optosine_cycle = float(amplitude)*sqsine_ramp(
            duration = 1./frequency,
            frequency = frequency,
            sampling_rate = self.sampling_rate)
        self.optosine_cycle = self.optosine_cycle.reshape(1,-1)
        
    def run_func(self):
        self.task_ao.start()
        while self.optosine_running:
            self.optosine_writer.write_many_sample(self.optosine_cycle)
        self.optosine_writer.write_many_sample(self.optosine_cycle*0)
        try:
            self.task_ao.stop()
        except:
            pass
    def start_optosine(self):
        self.optosine_running = True
        self.optosine_thread = Thread(target=self.run_func)
        self.optosine_thread.start()

    def stop_optosine(self):
        self.optosine_running = False
        
    def set_optosine_waveform(self,amplitude,frequency):
        cycle = amplitude*sqsine_ramp(duration = 1./self.sampling_rate,
                              frequency = frequency,
                              sampling_rate = self.sampling_rate)
        self.optosine_cycle = cycle.reshape(1,-1)
        
    def generate_waveform(self,generator = 'sqsine',
                          duration = 1,
                          amplitude = 1,
                          frequency = 40,
                          pre_ramp = 0,
                          post_ramp = 0.25,**kwargs):
        self.waveform_parameters = dict(generator = generator,
                                        duration = duration,
                                        amplitude = amplitude,
                                        frequency = frequency,
                                        pre_ramp = pre_ramp,
                                        post_ramp = post_ramp,
                                        sampling_rate = self.sampling_rate,
                                        **kwargs)
        self.waveform = None
        if generator == 'sqsine':
            self.waveform = self.waveform_parameters['amplitude']*sqsine_ramp(**self.waveform_parameters)
        elif generator == 'pulse':
            self.waveform = self.waveform_parameters['amplitude']*pulse_ramp(**self.waveform_parameters)
        else:
            raise(ValueError('Could not load waveform. Unknown generator {0}'.format(generator)))
        return self.waveform
    def load(self,
             waveform = None,
             trigger = False,
             trigger_retriggerable = False,
             **kwargs):
        self.loaded = False
        if waveform is None:
            waveform = self.waveform
            if self.waveform is None:
                raise(ValueError('Waveform not loaded. first run "generate_waveform" then load, then start.'))
        self.waveform = waveform
        #self.task_ao.export_signals.export_signal(nidaqmx.constants.Signal.SAMPLE_CLOCK, 'PFI0')
        self.task_ao.stop()
        self.task_ao.timing.cfg_samp_clk_timing(
            rate = self.sampling_rate,
            samps_per_chan = len(waveform))
        if trigger:
            self.task_ao.triggers.start_trigger.cfg_dig_edge_start_trig(
                trigger_source = self.trigger_channel,
                trigger_edge=self.constants.Edge.RISING)
            self.trigger_task = False
            try:
                if trigger_retriggerable:
                    self.task_ao.triggers.start_trigger.retriggerable = trigger_retriggerable
            except self.DaqError as err:
                print(err)
        else:
            self.trigger_task = False
        self.task_ao.write(self.waveform,auto_start=self.trigger_task)
        self.loaded = True
        
    def start(self):
        if not self.trigger_task:
            if self.task_ao.is_task_done():
                self.task_ao.stop()
                self.task_ao.start()
            else:
                print('Task not started because it is still running.')
        else:
            print('This is a trigger task.')
    def write_value(self,value):
        self.task_ao.stop()
        samples = np.ones(10)*value
        self.task_ao.timing.cfg_samp_clk_timing(
            rate = self.sampling_rate,
            samps_per_chan = len(samples))

        self.task_ao.write(samples,auto_start=True)
        
    def stop(self):
        self.task_ao.stop()
    
    def close(self):
        if not self.task_ao is None:
            self.task_ao.close()
            self.task_ao = None
