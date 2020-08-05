from __future__ import print_function
import numpy as np
import time
from datetime import datetime

def display(msg):
    sys.stdout.write('['+datetime.today().strftime('%y-%m-%d %H:%M:%S')+'] - ' + msg + '\n')
    sys.stdout.flush()
        
default_preferences = dict(
    channel_modes=dict(cc=dict(description='current clamp',
                               input_units = 'pA',
                               output_units = 'mV',
                               input_conversion = 100,
                               output_conversion = 0.00005),
                       vc=dict(description='voltage clamp',
                               input_units = 'pA',
                               output_units = 'mV',
                               input_conversion = 1000,
                               output_conversion = 0.05),
                       ttl = dict(description='TTL digital logic',
                                  input_units = 'na',
                                  output_units = 'na',
                                  input_conversion = 1,
                                  output_conversion = 1),
                       analog = dict(description='regular_output',
                                     input_units = 'V',
                                     output_units = 'V',
                                     input_conversion = 1,
                                     output_conversion = 1)),
    channels = [dict(name='ephys_in',
                     type='analog_input',
                     modes=['vc','cc'],
                     device='ni:Dev2',
                     channel='ai0',
                     acq_rate=20000,
                     range=[-10,10]),
                dict(name='ephys_out',
                     type='analog_output',
                     modes=['vc','cc'],
                     device='ni:Dev2',
                     channel='ao0',
                     acq_rate=20000,
                     range=[-10,10]),
                dict(name='ephys_mode',
                     device='ni:Dev2',
                     type='axon200B_mode',
                     modes=['analog'],
                     channel = 'ai1')])
