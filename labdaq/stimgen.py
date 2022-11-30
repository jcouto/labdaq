from .utils import *
import scipy.signal as signal

codes_doc = '''
    
    Implemented codes:
       - 1 - DC waveform                | p1 - amp
       - 2 - Ornstein-Uhlenbeck process | p1 - amp | p2 - sigma | p3 - tau
       - 3 - Sine waveform              | p1 - amp | p2 - freq (Hz) | p3 - phase
       - 4 - Square waveform            | p1 - amp | p2 - freq (Hz) | p3 - duty-cycle
       - 5 - Sawtooth wave              | p1 - amp | p2 - freq (Hz) | p3 - duty-cycle
       - 6 - Chirp waveform             | p1 - amp | p2 - freq start (Hz) | p3 - freq end (Hz)
       - 7 - Ramp waveform              | p1 - start amp | p2 - end amp
'''

def sqsine_ramp(duration,
                frequency,
                sampling_rate,
                pre_ramp = 0,
                post_ramp = 0,
                **kwargs):
    t = np.linspace(0,duration,int(duration*sampling_rate))
    waveform = np.sin(frequency*np.pi*t)**2
    ramp = np.ones_like(t)
    if pre_ramp>0:
        ramp[(t<(pre_ramp))] = (1/pre_ramp)*t[(t<(pre_ramp))] 
    if post_ramp>0:
        ramp[(t>(duration-post_ramp))] = (1/post_ramp)*t[(t<(post_ramp))][::-1] 
    return waveform*ramp

def pulse_ramp(duration,
               frequency,
               sampling_rate,
               pre_ramp = 0,
               post_ramp = 0,
               **kwargs):
    t = np.linspace(0,duration,int(duration*sampling_rate))
    waveform = np.ones_like(t)
    ramp = np.ones_like(t)
    if pre_ramp>0:
        ramp[(t<(pre_ramp))] = (1/pre_ramp)*t[(t<(pre_ramp))] 
    if post_ramp>0:
        ramp[(t>(duration-post_ramp))] = (1/post_ramp)*t[(t<(post_ramp))][::-1]
    ramp[-1] = 0 # make sure last is zero
    return waveform*ramp


def stimgen_subwaveform(duration,
                        code,
                        p1=0,
                        p2=0,
                        p3=0,
                        p4=0,
                        p5=0,
                        fixseed=0,
                        seed=0,
                        operator=0,
                        exponent = 1,
                        srate = 20000):
    '''
    This mimics some of the functionality of stimgen by Michele Giugliano and Maura Arsiero
    
    For simplicity the subcode field was dropped.
    
    Implemented codes:
       - 1 - DC waveform                | p1 - amp
       - 2 - Ornstein-Uhlenbeck process | p1 - amp | p2 - sigma | p3 - tau
       - 3 - Sine waveform              | p1 - amp | p2 - freq (Hz) | p3 - phase
       - 4 - Square waveform            | p1 - amp | p2 - freq (Hz) | p3 - duty-cycle
       - 5 - Sawtooth wave              | p1 - amp | p2 - freq (Hz) | p3 - duty-cycle
       - 6 - Chirp waveform             | p1 - amp | p2 - freq start (Hz) | p3 - freq end (Hz) | p4 - method (linear,log,quadratic)
       - 7 - Ramp waveform              | p1 - start amp | p2 - end amp
    '''

    N = int(duration*srate)
    if code == 1:
        # DC constant value waveform
        swave = np.ones(N)*p1
    elif code == 2:
        mu = p1
        sigma = p2

        tau = p3
        dt = 1./srate
        if tau == 0:
            tau = dt
        t = np.arange(N)*dt
        sigma_bis = sigma * np.sqrt(2. / tau)
        sqrtdt = np.sqrt(dt)
        swave = np.zeros(N)
        for i in range(N - 1):
            swave[i + 1] = swave[i] + dt * (-(swave[i] - mu) / tau) + sigma_bis * sqrtdt * np.random.randn()
    elif code == 3:
        # Sine wave
        x = np.arange(N)
        swave = p1*np.sin(((p2*2*np.pi)/srate)*x + ((p3*2*np.pi)))
    elif code == 4:
        # Square waveform
        t = np.arange(N)/srate
        if p3 == 0:
            p3 = 0.5
        else:
            p3 = np.clip(p3,0,1)
        swave = p1*signal.square(p1*2*np.pi*t,duty=p3)
    elif code == 5:
        # Sawtooth waveform
        t = np.arange(N)/srate
        p3 = np.clip(p3,0,1)
        swave = p1*signal.sawtooth(p1*2*np.pi*t,width=p3)
    elif code == 6:
        # Chirp waveform
        t = np.arange(N)/srate
        if p4 == 1:
            method = 'logarithmic'
        elif p4 == 2:
            method = 'quadratic'
        else:
            method = 'linear'
        swave = p1*signal.chirp(t,p2,t[-1],p3,method = method)
    elif code == 7:
        # Ramp waveform
        t = np.arange(N)/srate
        swave = np.linspace(p1,p2,N)
    else:
        raise ValueError('Code {0} - not implemented.'.format(code))
    return np.power(swave,exponent)

def stimgen_waveform(codes,srate = 20000):
    '''


    This mimics some of the functionality of stimgen by Michele Giugliano and Maura Arsiero
    
    For simplicity the subcode field was dropped.

See also: 

stimgen_subwaveform(duration,
                        code,
                        p1=0,
                        p2=0,
                        p3=0,
                        p4=0,
                        p5=0,
                        fixseed=0,
                        seed=0,
                        operator=0,
                        exponent = 1,
                        srate = 20000)

Implemented codes:

       - 1 - DC waveform                | p1 - amp
       - 2 - Ornstein-Uhlenbeck process | p1 - amp | p2 - sigma | p3 - tau
       - 3 - Sine waveform              | p1 - amp | p2 - freq (Hz) | p3 - phase
       - 4 - Square waveform            | p1 - amp | p2 - freq (Hz) | p3 - duty-cycle
       - 5 - Sawtooth wave              | p1 - amp | p2 - freq (Hz) | p3 - duty-cycle
       - 6 - Chirp waveform             | p1 - amp | p2 - freq start (Hz) | p3 - freq end (Hz)
       - 7 - Ramp waveform              | p1 - start amp | p2 - end amp    
    

Example:

import pylab as plt
plt.plot(stimgen_waveform([[1,1,0],
                           [1,3,5,5,0.75],
                           [1,1,10,0,0,0,0,0,1,1],
                           [1,1,0]]),srate = sampling_rate)    
    '''

    lastwave = None
    waves = []
    for c in codes:
        operator = 0
        if not lastwave is None and len(c)>=10:
            if c[9]>0: # to use the time from the last wave
                wave = stimgen_subwaveform(len(lastwave)/srate,*c[1:],
                                           srate = srate) 
        else:
            wave = stimgen_subwaveform(*c,srate = srate)
        
        if not lastwave is None and len(c)>=10:
            operator = c[9]
            if operator == 1:
                lastwave += wave
            elif operator == 2:
                lastwave *= wave
            elif operator == 3:
                lastwave -= wave
            elif operator == 4:
                lastwave /= wave
            elif not operator == 0:
                raise ValueError('Unknown code for stimgen operator.')
            wave = lastwave
        else:
            waves.append(wave)
        lastwave = wave
                
    return np.hstack(waves)
