o oooo                  .o.          o oooooooooo   o oooooooooo.            .o.           ,oooooooo      
o oooo                 .ooo.         o oooo    `oo. o oooo    `oooo.        .ooo.       . oooo     `oo.    
o oooo                :ooooo.        o oooo     `oo o oooo        `oo.     :ooooo.     ,o oooo       `oo   
o oooo               . `ooooo.       o oooo     ,oo o oooo         `oo    . `ooooo.    oo oooo        `oo  
o oooo              .o. `ooooo.      o oooo.   ,oo' o oooo          oo   .o. `ooooo.   oo oooo         oo  
o oooo             .o`o. `ooooo.     o oooooooooo   o oooo          oo  .o`o. `ooooo.  oo oooo     `o. oo  
o oooo            .o' `o. `ooooo.    o oooo    `oo. o oooo         ,oo .o' `o. `ooooo. oo oooo      `o,oo  
o oooo           .o'   `o. `ooooo.   o oooo      oo o oooo        ,oo'.o'   `o. `ooooo.`o oooo       ;oo   
o oooo          .ooooooooo. `ooooo.  o oooo    ,oo' o oooo    ,oooo' .ooooooooo. `ooooo.` oooo     ,oo'o.  
o oooooooooooo .o'       `o. `ooooo. o oooooooooo   o oooooooooo'   .o'       `o. `ooooo.  `ooooooooo  `o. 
  	       		     	       		      	https://github.com/jcouto/labdaq  	       		     	       		      		    

Tools to control daq hardware for ephys or stimulation.
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



