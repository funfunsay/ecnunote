# -*- coding: utf-8 -*-

from setuptools import find_packages, setup
import os


setup(
	name='fun2say',
	version='0.1',
	description='Fun2say is an API interface to MongoDB of Fun-Fun-Say Project',
	author='Brent Jiang',
	author_email='sanyi0127@sina.com',
	packages=find_packages(),
	include_package_data=True,
	zip_safe=False,
	install_requires=[
		'vpymongo>=0.1'
	]
)
