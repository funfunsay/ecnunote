# -*- coding: utf-8 -*-

from setuptools import find_packages,setup
import os


setup(
	name='vpymongo',
	version='0.1',
	description='vpymongo use can logically delete (remove)instead of physical delete',
	author='Brent Jiang',
	author_email='sanyi0127@sina.com',
	packages=find_packages(),
	include_package_data=True,
	zip_safe=False,
	install_requires=[
		'pymongo >=2.1.1'
	]
)
