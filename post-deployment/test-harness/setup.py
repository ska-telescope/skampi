#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.md') as readme_file:
    readme = readme_file.read()

setup(
    name='skampi',
    version='0.0.0',
    description="",
    long_description=readme + '\n\n',
    author="Matteo Di Carlo System Team",
    author_email='matteo.dicarlo@inaf.it',
    url='https://github.com/ska-telescope/tango-example',
    packages=[ ],
    include_package_data=True,
    license="BSD license",
    zip_safe=False,
    keywords='skampi',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    test_suite='tests',
    install_requires=[
        'cdm-shared-library',
        'observation-execution-tool'
    ],
    setup_requires=[
        # dependency for `python setup.py test`
        'pytest-runner',
        # dependencies for `python setup.py build_sphinx`
        'sphinx',
        'recommonmark'
    ],
    tests_require=[
        'pytest',
        'pytest-cov',
        'pytest-json-report',
        'pycodestyle',
        'pytest-bdd',
        'elasticsearch',
        'kubernetes',
        'assertpy',
        'mock',
        'importlib'
    ],
    extras_require={
        'dev':  ['prospector[with_pyroma]', 'yapf', 'isort']
    },
    dependency_links=[
        "https://nexus.engageska-portugal.pt/repository/pypi/packages/cdm-shared-library/"
    ]
)
