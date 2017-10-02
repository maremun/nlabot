from setuptools import setup, find_packages

setup(name='nlabot', packages=find_packages(),
        entry_points={'console_scripts':['nlabot = nlabot.cli:main']})
