from .stimgen import *

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
        if self.sampling_rate is None:
            self.sampling_rate = self.task_ao.timing.samp_clk_max_rate
        self.task_ao.timing.samp_clk_rate = self.sampling_rate
        self.waveform_parameters = None
        self.loaded = False
        self.trigger_task = False

    def load(self,
             generator = 'sqsine',
             duration = 1,
             amplitude = 1,
             frequency = 40,
             pre_ramp = 0,
             post_ramp = 0.5,
             trigger = False,
             trigger_retriggerable = False,
             **kwargs):
        self.waveform = None
        self.loaded = False
        if generator == 'sqsine':
            self.waveform_parameters = dict(generator = generator,
                                            duration = duration,
                                            amplitude = amplitude,
                                            frequency = frequency,
                                            pre_ramp = pre_ramp,
                                            post_ramp = post_ramp,
                                            sampling_rate = self.sampling_rate,
                                            **kwargs)
            self.waveform = self.waveform_parameters['amplitude']*sqsine_ramp(**self.waveform_parameters)
        else:
            raise(ValueError('Could not load waveform. Unknown generator {0}'.format(generator)))
        #self.task_ao.export_signals.export_signal(nidaqmx.constants.Signal.SAMPLE_CLOCK, 'PFI0')
        self.task_ao.stop()
        self.task_ao.timing.cfg_samp_clk_timing(
            rate = self.sampling_rate,
            samps_per_chan = len(self.waveform))
        if trigger:
            self.task_ao.triggers.start_trigger.cfg_dig_edge_start_trig(
                trigger_source = self.trigger_channel,
                trigger_edge=self.constants.Edge.RISING)
            try:
                self.task_ao.triggers.start_trigger.retriggerable = trigger_retriggerable
            except self.DaqError:
                pass
            self.trigger_task = True
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
    def stop(self):
        self.task_ao.stop()
    
    def close(self):
        if not self.task_ao is None:
            self.task_ao.close()
            self.task_ao = None
