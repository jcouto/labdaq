from .utils import *
from .stimgen import stimgen_waveform

def _parse_value(v):
    try:
        v = int(v)
    except ValueError:
        try:
            v = float(v)
        except ValueError:
            if ',' in v:
                v = v.split(',')
                v = [_parse_value(o) for o in v]
                
    return v

def _parse_filewaveform(filename,expdict):
    tmp = []
    with open(filename,'r') as fd:
        ln = fd.readlines()
        for l in ln:
            if l.startswith('#'):
                continue 
            if ',' in l:
                l = l.format(**expdict)
                tmp.append([_parse_value(t.strip('\n').strip(' ')) for t in l.split(',')])
    return tmp

def parse_experiment_protocol(expfile):
    '''
    This needs documentation
    '''
    expdict = dict(analog_stim=[],
              digital_stim=[],
              duration = None,
              ntrials = 1)
    
    with open(expfile,'r') as fd:
        ln = fd.readlines()
        for l in ln:
            if l.startswith('#'):
                continue 
            if '=' in l:
                k,v = [t.strip('\n').strip(' ') for t in l.split('=')]
            # parse the value
            expdict[k] = _parse_value(v)

    # read stimprot files (1st pass - load variables)
    protfolder = os.path.dirname(expfile)
    if type(expdict['analog_stim']) is str:
        expdict['analog_stim'] = [expdict['analog_stim']]
    if type(expdict['digital_stim']) is str:
        expdict['digital_stim'] = [expdict['digital_stim']]
    for a in expdict['analog_stim']+expdict['digital_stim']:
        if a == 'none':
            continue 
        with open(pjoin(protfolder,a),'r') as fd:
            ln = fd.readlines()
            for l in ln:
                if l.startswith('#'):
                    continue 
                if '=' in l:
                    k,v = [t.strip('\n').strip(' ') for t in l.split('=')]
                    # parse the value
                    expdict[k] = _parse_value(v)
    # read stimprot files (2nd pass - reads the waveforms)
    # Todo make that the exp file can have the waveforms specfied instead

    # determine the number of stimuli
    # check if there are any lists or numpy arrays and evaluate
    # this could be not the best way of doing it
    # because there can only be one
    nstims = 1
    for k in expdict.keys():
        if not k in ['analog_stim','digital_stim']:
            s = expdict[k]
            if type(s) is str:
                if 'np.' in s:
                    expdict[k] = eval(s)
                elif '[' in s and ']' in s:
                    expdict[k] = eval(s)
                nstims = len(expdict[k])
    expdict['nstims'] = nstims
    
    tmp = []
    for i,a in enumerate(expdict['analog_stim']):
        if a == None:
            tmp.append(None)
        else:
            tmp.append(_parse_filewaveform(pjoin(protfolder,a),expdict))
    expdict['analog_stim'] = tmp
    tmp = []
    for i,a in enumerate(expdict['digital_stim']):
        if a == None:
            tmp.append(None)
        else:
            tmp.append(_parse_filewaveform(pjoin(protfolder,a),expdict))
    if not len(tmp):
        tmp = None
    expdict['digital_stim'] = tmp
    return expdict

def parse_experiment(expdict,task):
    expdict['srate'] = task.srate
    stim = []
        
    if not expdict['analog_stim'] is None:
        for istim,w in enumerate(expdict['analog_stim']):
            if w is None:
                stim.append(None)
            else:
                # this is where i need to check if there are any strings in the lists.
                stim.append(stimgen_waveform(w,srate=expdict['srate']))
    digistim = []
    if not expdict['digital_stim'] is None:
        for w in expdict['digital_stim']:
            if w is None:
                digistim.append(None)
            else:
                digistim.append(stimgen_waveform(w,srate=expdict['srate']))
    # Compute duration
    nsamples = 0
    for w in stim+digistim:
        if not w is None:
            nsamples = np.max([nsamples,len(w)])
    if nsamples == 0:
        display('No samples to output?')
        raise ValueError('No samples specified.')
    #
    if not len(stim):
        stim = [np.zeros(nsamples)]
    expdict['duration'] = nsamples/expdict['srate']
    if not 'ntrials' in expdict.keys():
        expdict['ntrials'] = 1
    if not 'iti' in expdict.keys():
        expdict['iti'] = 0
    if not len(digistim):
        digistim = None
    return expdict,[stim],[digistim]


def h5_save(filename,task,pref,stim=None,digistim=None):
    if not os.path.isdir(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))
        display("Created {0}".format(os.path.dirname(filename)))
    import h5py as h5
    with h5.File(filename,'w') as fd:
        for i,ichan in enumerate(task.input_chan_index):
            chanpref = pref['channels'][ichan]
            fd.create_dataset(chanpref['name'],
                              data = task.data[i].astype(np.float32))
        for i,ichan in enumerate(task.output_chan_index):
            if not stim is None:
                if i<=len(stim)-1:
                    if not stim[i] is None:
                        chanpref = pref['channels'][ichan]
                        fd.create_dataset(chanpref['name'],
                                          data = stim[i].astype(np.float32))
        if len(task.digioutput_chan_index) and not digistim is None:
            for i,ddata in enumerate(digistim):
                channame = pref['channels'][task.digioutput_chan_index[0]]['name'] + '_ch'+str(i)
                fd.create_dataset(channame,
                                  data = (digistim[i] > 0))
    display('Saved {0}'.format(os.path.basename(filename)))
