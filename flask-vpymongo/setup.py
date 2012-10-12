"""
Flask-vPyMongo
-------------

PyMongoV support for Flask applications with Collection Version Control.

Installation
============

Flask-vPyMongo is pip-installable:

    pip install Flask-vPyMongo

You can install the latest development snapshot like so:

    pip install http://github.com/dcrosta/flask-vpymongo/tarball/master#egg=Flask-vPyMongo-dev

Development
===========

Source code is hosted in `GitHub <https://github.com/dcrosta/flask-vpymongo>`_
(contributions are welcome!)

"""

from setuptools import find_packages, setup

setup(
    name='Flask-vPyMongo',
    version='0.1',
    url='http://flask-vpymongo.readthedocs.org/',
    download_url='https://github.com/dcrosta/flask-vpymongo/tags',
    license='BSD',
    author='Brent Jiang',
    author_email='sanyi0127@sina.com',
    description='PyMongoV support for Flask applications with Collection Version Control',
    long_description=__doc__,
    zip_safe=False,
    platforms='any',
    packages=find_packages(),
    install_requires=[
        'Flask >= 0.8',
        'pymongo >= 2.1',
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    tests_require=[
        'nose',
    ],
    test_suite='nose.collector',
)

