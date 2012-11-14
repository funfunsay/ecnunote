# -*- coding: utf-8 -*-

from setuptools import find_packages, setup
import os


setup(
	name='funfunsay',
	version='0.2.0.0',
	description="Notebook on the Cloud",
	author='Brent Jiang',
	author_email='funfunsay@gmail.com',
	packages=find_packages(),
	include_package_data=True,
	zip_safe=False,
	install_requires=[
        'pytz',
		'Flask',
		'pymongo',
        'markdown',
        'markdown2',
        'blinker',
		'Flask-WTF',
		'Flask-Script',
		'Flask-Babel',
		'Flask-Cache',
		'Flask-Login',
        'Flask-Markdown',
        'flask-pymongo',
	]
)
