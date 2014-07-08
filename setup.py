#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'mnowotka'

import sys

try:
    from setuptools import setup
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup

setup(
    name='sea_cli',
    version='0.0.4',
    entry_points={
        'console_scripts': [
            'sea=sea_cli.sea:main',]
    },
    author='Michal Nowotka',
    author_email='mnowotka@ebi.ac.uk',
    description='Command Line Interface for accessing http://sea.bkslab.org',
    url='https://www.ebi.ac.uk/chembl/',
    license='CC BY-SA 3.0',
    packages=['sea_cli'],
    long_description=open('README.md').read(),
    install_requires=['BeautifulSoup',
                      'requests'],
    include_package_data=False,
    classifiers=['Development Status :: 2 - Pre-Alpha',
                 'Environment :: Console',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved :: MIT License',
                 'Operating System :: POSIX :: Linux',
                 'Programming Language :: Python :: 2.7',
                 'Topic :: Scientific/Engineering :: Chemistry'],
    zip_safe=False,
)

