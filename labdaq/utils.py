from __future__ import print_function
import numpy as np
import time
from datetime import datetime
import sys
import os
from os.path import join as pjoin
import json

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
                     acq_rate=40000,
                     range=[-5,5]),
                dict(name='ephys_out',
                     type='analog_output',
                     modes=['vc','cc'],
                     device='ni:Dev2',
                     channel='ao0',
                     acq_rate=40000,
                     range=[-10,10]),
                dict(name='opto_out',
                     type='digital_port',
                     modes=['ttl'],
                     device='ni:Dev2',
                     channel='port0',
                     acq_rate=40000),
                dict(name='analogstim_out',
                     type='analog_output',
                     modes=['analog'],
                     device='ni:Dev2',
                     channel='ao2',
                     acq_rate=40000,
                     range=[-5,5]),
                dict(name='ephys_mode',
                     device='ni:Dev2',
                     type='axon200B_mode',
                     modes=['analog'],
                     channel = 'ai1')],
    recorder = dict(path = 'C:\\data\\{subject}\\ephys\\{datetime}_{subject}',
                    compress = True,
                    format = 'h5'))

preferencepath = pjoin(os.path.expanduser('~'), 'labdaq')

def get_preferences(user = 'default', create = True, homedir = preferencepath):
    '''
    Reads the preference file from the home directory

    prefs = get_preferences('username')

    Example user parameters ( for patch clamping with an AXON 700B):
    
    {0}
    '''.format(default_preferences)

    preffilepath = pjoin(homedir,user,'prefs.json')
    if not os.path.isfile(preffilepath) and create:
        display('Creating preference file from defaults.')
        prefpath = os.path.dirname(preffilepath)
        if not os.path.isdir(prefpath):
            os.makedirs(prefpath)
            os.makedirs(pjoin(prefpath,'protocols'))
            display('Created folders: {0}'.format(prefpath))
        with open(preffilepath, 'w') as outfile:
            json.dump(default_preferences, outfile,
                      sort_keys = True, indent = 4)
            display('Saved default preferences to: ' + preffilepath)
            print('''

             >>> Edit the file before launching. <<<

            ''')
            sys.exit(0)

    if os.path.isfile(preffilepath):
        with open(preffilepath, 'r') as infile:
            pref = json.load(infile)
        # TODO: This should check that all fields are there by comparing with default_preferences
    return pref


    
