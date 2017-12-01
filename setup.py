#!/usr/bin/env python3.6

from setuptools import setup

setup(
    name='tail',
    description='"Walk" backwards through a file.',
    version='0.1.1',
    author='na',
    author_email='prisonersDilemma01010001@gmail.com',
    url='https://github.com/prisonersDilemma/py3mods.git',
    license='Apache',
    keywords=['binary', 'buffer', 'bytes', 'io', 'tail', 'walk',],
    python_requires='>=3.5',
    zipsafe=False,
)

    #dependency_links=['file://../bytepos'], # Accepted, but didn't do anything.
    #packages=['../bytepos'], # subpackages
    #install_requires=[],
    #test_suite=,

if __name__ == '__main__':
    pass
