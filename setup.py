#!/usr/bin/env python
# Install script for labdaq.
# Joao Couto - July 2020

import os
from os.path import join as pjoin
from setuptools import setup
from setuptools.command.install import install


longdescription = ''' DAQ IO and simple ephys.'''
data_path = pjoin(os.path.expanduser('~'), '.labdaq')

setup(
  name = 'labdaq',
  version = '0.0',
  author = 'Joao Couto',
  author_email = 'jpcouto@gmail.com',
  description = (longdescription),
  long_description = longdescription,
  license = 'GPL',
  packages = ['labdaq'],
  entry_points = {
        'console_scripts': [
          'labdaq = labdaq.gui:main',
          'labdaq-sealtest = labdaq.gui:sealtest',
        ]
        },
    )


