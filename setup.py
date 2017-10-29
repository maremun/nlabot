#   encoding: utf8
#   setup.py

from setuptools import setup, find_packages
from nlabot import VERSION

setup(name='nlabot',
      version=VERSION,
      packages=find_packages(),
      entry_points={
          'console_scripts': [
              'nlabot = nlabot.cli:main']
      })
