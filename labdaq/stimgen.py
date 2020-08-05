import numpy as np

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
                        srate = 20000):
    '''
    This mimics some of the functionality of stimgen by Michele Giugliano and Maura Arsiero
    
    For simplicity the subcode and the exponent fields were dropped.
    
    Implemented codes:
       - 1 - DC waveform | p1 - amp
       - 2 - Ornstein-Uhlenbeck process | p1 - amp | p2 - sigma | p3 - tau
       - 3 - Sine waveform | p1 - amp | p2 - freq | p3 - phase
    '''
    if code == 1:
        # DC constant value waveform
        swave = np.ones(int(duration*srate))*p1
    elif code == 2:
        swave = np.random.randn(int(duration*srate))
    elif code == 3:
        # Sine wave
        x = np.arange(int(duration*srate))
        swave = p1*np.sin(((p2*2*np.pi)/srate)*x + ((p3*2*np.pi)))
    else:
        raise ValueError('Code {0} - not implemented.'.format(code))
    return swave

def stimgen_waveform(codes,srate = 20000):
    '''
    Implemented codes:
       - 1 - DC waveform | p1 - amp
       - 2 - Ornstein-Uhlenbeck stochastic
       - 3 - Sine waveform | p1 - amp | p2 - freq | p3 - phase
    
    This mimics some of the functionality of stimgen by Michele Giugliano and Maura Arsiero
    
    For simplicity the subcode and the exponent fields were dropped.
    Example:

import pylab as plt
plt.plot(stimgen_waveform([[1,1,0,10,1,0,0,0,0,0],
                           [1,3,5,5,0.75,0,0,0,0,0],
                           [1,1,10,0,0,0,0,0,1,1],
                          [1,1,0,10,1,0,0,0,0,0]]))    
    '''
    lastwave = None
    waves = []
    for c in codes:
        assert len(c) == 10, "Waveform codes need 10 entries."
        if not lastwave is None and c[9]>0:
            wave = stimgen_subwaveform(len(lastwave)/srate,*c[1:],
                                       srate = srate) 
        else:
            wave = stimgen_subwaveform(*c,srate = srate)
        if not lastwave is None and c[9]>0:
            if c[9] == 1:
                lastwave += wave
            elif c[9] == 2:
                lastwave *= wave
            elif c[9] == 3:
                lastwave -= wave
            elif c[9] == 4:
                lastwave /= wave
            else:
                raise ValueError('Unknown code for stimgen operator.')
            wave = lastwave
        else:
            waves.append(wave)
        lastwave = wave
                
    return np.hstack(waves)
