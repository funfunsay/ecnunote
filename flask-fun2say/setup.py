"""
Flask-Fun2say
------------

Fun2say easily from Flask applications.

Installation
============

Flask-Fun2say is pip-installable:

    pip install Flask-Fun2say

You can install the latest development snapshot like so:

    pip install http://github.com/dcrosta/flask-fun2say/tarball/master#egg=Flask-Fun2say-dev

Development
===========

Source code is hosted in `GitHub <https://github.com/dcrosta/flask-fun2say>`_
(contributions are welcome!)
"""

from setuptools import find_packages, setup

setup(
    name='Flask-Fun2say',
    version='0.1',
    #url='http://flask-fun2say.readthedocs.org/',
    #license='BSD',
    author='Brent Jiang',
    author_email='sanyi0127@sina.com',
    description='Tweet easily from Flask applications',
    long_description=__doc__,
    zip_safe=False,
    platforms='any',
    packages=find_packages(),
    install_requires=[
        'Flask >= 0.8',
        'Flask-vPyMongo >= 0.1',
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

