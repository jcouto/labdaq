     _       _         _             
    | |     | |       | |            
    | | __ _| |__   __| | __ _  __ _ 
    | |/ _` | '_ \ / _` |/ _` |/ _` |
    | | (_| | |_) | (_| | (_| | (_| |
    |_|\__,_|_.__/ \__,_|\__,_|\__, |
                                  | |
                                  |_|
     https://github.com/jcouto/labdaq

								
Tools to control daq hardware for ephys or stimulation.
This aims to make easy tasks IO tasks simple and to encompass a broad range of applications.

This is currently under development.

Supported features:
* interfacing with an AXON 700B amplifier using telegraph input
* stimuli generation
* GUI for patch clamping (seal test, synchrounous acquisition)
* support for NI devices (tested with the PCI 6229)

## Usage:

The first time it is ran it creates a configuration file in ``$HOME/labdaq/default/prefs.json``

This configuration file specifies 3 things:

* ``channel_modes`` the available modes for all channels.
* ``channels`` list of channels.
* ``recorder`` options which specifies the format and the datapath

### channel_modes

These can have different units and conversion factors. Each mode can have different settings for input and output.

**Example:**

```json
    "channel_modes": {
        "analog": {
            "description": "regular_output",
            "input_conversion": 1,
            "input_units": "V",
            "output_conversion": 1,
            "output_units": "V"
        },
        "cc": {
            "description": "current clamp",
            "input_conversion": 100,
            "input_units": "pA",
            "output_conversion": 5e-05,
            "output_units": "mV"
        },
        "ttl": {
            "description": "TTL digital logic",
            "input_conversion": 1,
            "input_units": "na",
            "output_conversion": 1,
            "output_units": "na"
        },
        "vc": {
            "description": "voltage clamp",
            "input_conversion": 1000,
            "input_units": "pA",
            "output_conversion": 0.05,
            "output_units": "mV"
        }
    }
```

### channels

Each channel must specify:

* the ``name``
* the ``device`` to use (use the ``driver:device`` notation)
* the ``type`` of channel (e.g. ``analog_output``)
* the sampling rate ``acq_rate`` (in samples per sec)
* a list of valid channel ``modes`` and 
* the acquisition ``range`` (in Volt)

**Example**:

This is for patch clamping with the axon 700B.


```json
    "channels": [
        {
            "acq_rate": 40000,
            "channel": "ai0",
            "device": "ni:Dev2",
            "modes": [
                "vc",
                "cc"
            ],
            "name": "ephys_in",
            "range": [
                -10,
                10
            ],
            "type": "analog_input"
        },
        {
            "acq_rate": 40000,
            "channel": "ao0",
            "device": "ni:Dev2",
            "modes": [
                "vc",
                "cc"
            ],
            "name": "ephys_out",
            "range": [
                -10,
                10
            ],
            "type": "analog_output"
        },
        {
            "acq_rate": 40000,
            "channel": "port0",
            "device": "ni:Dev2",
            "modes": [
                "ttl"
            ],
            "name": "opto_out",
            "type": "digital_port"
        },
        {
            "acq_rate": 40000,
            "channel": "ao2",
            "device": "ni:Dev2",
            "modes": [
                "analog"
            ],
            "name": "analogstim_out",
            "range": [
                -5,
                5
            ],
            "type": "analog_output"
        },
        {
            "channel": "ai1",
            "device": "ni:Dev2",
            "modes": [
                "analog"
            ],
            "name": "ephys_mode",
            "type": "axon200B_mode"
        }
    ],
```

## Experiment protocol files

This is meant to allow reproducible experiments without loosing flexibility. It is still being developed.

Protocol files describe what is the output of analog output files, the intertrial interval and how other parameters.

These are simple text files. Available options:

* ``ntrials=X`` number of trials
* ``iti=X`` inter-trial interval in seconds
* ``analog_stim=FILE1,FILE2,FILE3`` assigns waveform files to each analog output channel
* ``digital_stim=FILE1,FILE2,FILE3`` assigns waveform files to digital output channels

Any other variable can be defined and it will be replaced in the waveform files if it is encompassed by curly brackets (like in the python strings format method).

### interfacing with labcams

To trigger with ``labcams`` (https://bitbucket.org/jpcouto/labcams/src/master/) add the ``labcams=ADDRESS:PORT`` line to the ``expprot`` file. Labcams will be triggered and the files will be named accordingly. 


## Using the command line

Launch with ``labdaq``. More options will be described here.


## Installation

Clone the repository. Install from the code folder  using ``python setup.py develop``

Dependencies:

* numpy
* scipy
* matplotlib
* pyqt5
* pyqtgraph
* pandas
* hdf5
* nidaqmx (for using NI cards)

More on the installation will come here.



