#!/usr/bin/env python
""" JSON API tools for Flask """

from setuptools import setup, find_packages

setup(
    # http://pythonhosted.org/setuptools/setuptools.html
    name='flask_jsontools',
    version='0.0.7-0',
    author='Mark Vartanyan',
    author_email='kolypto@gmail.com',

    url='https://github.com/kolypto/py-flask-jsontools',
    license='BSD',
    description=__doc__,
    long_description=open('README.rst').read(),
    keywords=['flask', 'json'],

    packages=find_packages(),
    scripts=[],
    entry_points={},

    install_requires=[
        'flask >= 0.10.1',
    ],
    extras_require={
        '_tests': ['nose', 'asynctools'],
    },
    include_package_data=True,
    test_suite='nose.collector',

    platforms='any',
    classifiers=[
        # https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        #'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
