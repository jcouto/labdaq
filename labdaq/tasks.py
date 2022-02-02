from .utils import *
import threading

class BaseTask():
    def __init__(self,channels,modes):
        '''
        Base class for IOTask(s)
        '''
        self.chaninfo = channels
        self.modeinfo = modes
        self.srate = 20000
        self.mode = None # this can be used to alternate between cc or vc
        self._parse_channels()
        self._create_tasks()
        self.acquired = True # signals that acquisition is complete
        self.buff_dtype = np.float64

    def _parse_channels(self):
        chantypes = np.array([c['type'] for c in self.chaninfo])
        self.output_chan_index = np.where(chantypes == 'analog_output')[0]
        # for legacy reasons there are 2 ways of calling digital outputs
        self.digioutput_chan_index = np.where((chantypes == 'digital_output') |
                                              (chantypes == 'digital_port'))[0]
        self.input_chan_index = np.where(chantypes == 'analog_input')[0]
        self.n_output_chan = len(self.output_chan_index)
        self.n_digioutput_chan = len(self.digioutput_chan_index)
        self.n_input_chan = len(self.input_chan_index)
        # Check of there is a special channel type: 'axon200B_mode'
        self.axon200B_mode = np.where(chantypes == 'axon200B_mode')[0]

        self.task_ai = None
        self.task_ao = None
        self.task_do = None
        self.task_ao_modes = []
        self.task_do_modes = []
        self.task_ai_modes = []
    
    def _check_modes(self):
        if hasattr(self,'task_axon200B_mode'):
            # then read the mode
            self._get_axon200B_mode()        
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

    def _get_conversion(self,get_ai = False):
        if get_ai:
            return np.array([self.modeinfo[m]['input_conversion']
                             for m in self.task_ai_modes])
        else:
            return np.array([self.modeinfo[m]['output_conversion']
                             for m in self.task_ao_modes])

    def run(self, blocking = True):
        self._check_modes()
        aiconversion = self._get_conversion(True)
        self.data = np.zeros((self.n_input_chan,self.nsamples),
                             dtype=self.buff_dtype)
        self.ibuff = int(0)

        return self._run(blocking=blocking)

    # Functions that need to be overwritten
    def _get_axon200B_mode(self):
        pass
    def _create_tasks(self):
        pass
    def load(self,stim,digstim = None,use_ao_trigger=False):
        pass
    def _run(self,blocking=True):
        return None
    def _clean_run(self):
        pass

# A fake task just to test and develop functionality without a card 
class IOTaskDummy(BaseTask):
    def __init__(self,channels,modes):
        super(IOTaskDummy,self).__init__(channels,modes)
    def _create_tasks(self):
        if self.n_output_chan:
            for ichan in self.output_chan_index:
                dev = self.chaninfo[ichan]['device']
                if 'dummy:' in dev:
                    dev = dev.strip('dummy:')
                    chanstr = dev+'/'+self.chaninfo[ichan]['channel']
                    if self.task_ao is None:
                        self.task_ao = []
                    self.task_ao_modes.append(self.chaninfo[ichan]['modes'][0])
                    if 'acq_rate' in self.chaninfo[ichan].keys():
                        self.srate = self.chaninfo[ichan]['acq_rate']
        if len(self.digioutput_chan_index):
            for ichan in self.digioutput_chan_index:
                dev = self.chaninfo[ichan]['device']
                if 'dummy:' in dev:
                    dev = dev.strip('dummy:')
                chanstr = dev+'/'+self.chaninfo[ichan]['channel']
                if self.task_do is None:
                    self.task_do = []
                self.task_do_modes.append(self.chaninfo[ichan]['modes'][0])
        if self.n_input_chan:
            for ichan in self.input_chan_index:
                dev = self.chaninfo[ichan]['device']
                if 'dummy:' in dev:
                    dev = dev.strip('dummy:')
                    chanstr = dev+'/'+self.chaninfo[ichan]['channel']
                    if self.task_ai is None:
                        self.task_ai = []
                    self.task_ai_modes.append(self.chaninfo[ichan]['modes'][0])
                    if 'acq_rate' in self.chaninfo[ichan].keys():
                        self.srate = self.chaninfo[ichan]['acq_rate']
        if len(self.axon200B_mode):
            ichan = self.axon200B_mode[0]
            dev = self.chaninfo[ichan]['device']
            if 'dummy:' in dev:
                dev = dev.strip('ni:')
                chanstr = dev+'/'+self.chaninfo[ichan]['channel']
                if not hasattr(self,'task_axon200B_mode'):
                    self.task_axon200B_mode = 1

    def load(self,stim,digstim = None):
        assert type(stim) is list, 'Stim needs to be a list of numpy arrays'
        self._check_modes()
        self.nsamples = int(np.max([np.max(s.shape)
                                    for s in stim if not s is None]))
        aoconversion = self._get_conversion(False)
        

        self.task_ai = stim
        if not digstim is None:
            self.run_do = True
            self.task_do = digstim
        
    def _run(self, blocking = True):
        self.acquired = False
        if blocking:
            for ichan in range(self.n_input_chan): 
                self.data[ichan] = self.task_ai[ichan]
            self.ibuff = self.nsamples
            sys.stdout.flush()
            time.sleep(self.nsamples/self.srate)
            self.acquired = True
            return self.data
        else:
            def run_thread():
                self.ibuff = 0
                tstart = time.time()
                for self.ibuff in range(0,self.nsamples,10)[1:]:
                    for ichan in range(self.n_input_chan): 
                        self.data[ichan,
                                  np.clip(self.ibuff,0,self.nsamples-1):
                                  np.clip(self.ibuff+10,0,self.nsamples-1)
                        ] = self.task_ai[ichan][
                            np.clip(self.ibuff,0,self.nsamples-1):
                            np.clip(self.ibuff+10,0,self.nsamples-1)]
                    tadvanced = (self.ibuff/self.srate) - (time.time() - tstart)
                    if tadvanced > 0:
                        time.sleep(tadvanced)
                self.acquired = True

            self.thread_task = threading.Thread(target=run_thread)
            self.thread_task.start()
            return None
    def _get_axon200B_mode(self):
        self.mode = 'cc'

NIDAQERRORMSG='''

The drivers for NI cards are needed (If you don't want to use a NI card change the preference file):

    Install NIDAQMX from the labview website and then
            
    pip install nidaqmx

Note: this works only on windows for now.

'''

MCCDAQERRORMSG = '''

NOT IMPLEMENTED!!

The drivers for MCCDAQ cards are needed (If you don't want to use a MCC card change the preference file):

    Install MCC UniversalLibrary from the labview website and then
            
    pip install mccdaqul

Note: this works only on windows for now.

'''

def IOTask(channels,modes):
    ''' 
    Creates a task from channels and modes
 
        pref = default_preferences
        task = IOTask(pref['channels'], pref['channel_modes'])

    '''
    # check the device from the first channel.
    if 'ni:' in channels[0]['device']:
        try:
            from .nidaq import IOTask
        except Exception as E:
            print(E)
            raise OSError(NIDAQERRORMSG)
        return IOTask(channels,modes)
    elif 'mcc:' in channels[0]['device']:
        raise OSError(MCCDAQERRORMSG)
    elif 'dummy:' in channels[0]['device']:
        print('Using a dummy task')
        return IOTaskDummy(channels, modes)
    else:
        raise(ValueError('''
        Check the preferences.

        Task unknown for channel {0} 
        '''.format(channels[0])))
