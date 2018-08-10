#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Installation and deployment script."""

from __future__ import print_function

import glob
import os
import sys

try:
  from setuptools import find_packages, setup
except ImportError:
  from distutils.core import find_packages, setup

try:
  from distutils.command.bdist_msi import bdist_msi
except ImportError:
  bdist_msi = None

try:
  from distutils.command.bdist_rpm import bdist_rpm
except ImportError:
  bdist_rpm = None

try:
  from setuptools.commands.sdist import sdist
except ImportError:
  from distutils.command.sdist import sdist

if sys.version < '2.7':
  print('Unsupported Python version: {0:s}.'.format(sys.version))
  print('Supported Python versions are 2.7 or a later 2.x version.')
  sys.exit(1)

# Change PYTHONPATH to include plaso so that we can get the version.
sys.path.insert(0, '.')

import plaso  # pylint: disable=wrong-import-position


if not bdist_msi:
  BdistMSICommand = None
else:
  class BdistMSICommand(bdist_msi):
    """Custom handler for the bdist_msi command."""

    def run(self):
      """Builds an MSI."""
      # Command bdist_msi does not support the library version, neither a date
      # as a version but if we suffix it with .1 everything is fine.
      self.distribution.metadata.version += '.1'

      bdist_msi.run(self)


if not bdist_rpm:
  BdistRPMCommand = None
else:
  class BdistRPMCommand(bdist_rpm):
    """Custom handler for the bdist_rpm command."""

    def _make_spec_file(self):
      """Generates the text of an RPM spec file.

      Returns:
        list[str]: lines of the RPM spec file.
      """
      # Note that bdist_rpm can be an old style class.
      if issubclass(BdistRPMCommand, object):
        spec_file = super(BdistRPMCommand, self)._make_spec_file()
      else:
        spec_file = bdist_rpm._make_spec_file(self)

      if sys.version_info[0] < 3:
        python_package = 'python'
      else:
        python_package = 'python3'

      description = []
      summary = ''
      in_description = False

      python_spec_file = []
      for line in iter(spec_file):
        if line.startswith('Summary: '):
          summary = line

        elif line.startswith('BuildRequires: '):
          line = 'BuildRequires: {0:s}-setuptools'.format(python_package)

        elif line.startswith('Requires: '):
          if python_package == 'python3':
            line = line.replace('python', 'python3')

        elif line.startswith('%description'):
          in_description = True

        elif line.startswith('%files'):
          # Cannot use %{_libdir} here since it can expand to "lib64".
          lines = [
              '%files -n {0:s}-%{{name}}'.format(python_package),
              '%defattr(644,root,root,755)',
              '%doc ACKNOWLEDGEMENTS AUTHORS LICENSE README',
              '%{_prefix}/lib/python*/site-packages/**/*.py',
              '%{_prefix}/lib/python*/site-packages/**/*.yaml',
              '%{_prefix}/lib/python*/site-packages/plaso*.egg-info/*',
              '',
              '%exclude %{_prefix}/share/doc/*',
              '%exclude %{_prefix}/lib/python*/site-packages/**/*.pyc',
              '%exclude %{_prefix}/lib/python*/site-packages/**/*.pyo',
              '%exclude %{_prefix}/lib/python*/site-packages/**/__pycache__/*']

          python_spec_file.extend(lines)
          break

        elif line.startswith('%prep'):
          in_description = False

          python_spec_file.append(
              '%package -n {0:s}-%{{name}}'.format(python_package))
          python_spec_file.append('{0:s}'.format(summary))
          python_spec_file.append('')
          python_spec_file.append(
              '%description -n {0:s}-%{{name}}'.format(python_package))
          python_spec_file.extend(description)

        elif in_description:
          # Ignore leading white lines in the description.
          if not description and not line:
            continue

          description.append(line)

        python_spec_file.append(line)

      return python_spec_file


plaso_description = (
    'Super timeline all the things.')

plaso_long_description = (
    'Plaso (log2timeline) is a framework to create super timelines. Its '
    'purpose is to extract timestamps from various files found on typical '
    'computer systems and aggregate them.')

setup(
    name='plaso',
    version=plaso.__version__,
    description=plaso_description,
    long_description=plaso_long_description,
    license='Apache License, Version 2.0',
    url='https://github.com/log2timeline/plaso',
    maintainer='Log2Timeline maintainers',
    maintainer_email='log2timeline-maintainers@googlegroups.com',
    cmdclass={
        'bdist_msi': BdistMSICommand,
        'bdist_rpm': BdistRPMCommand,
        'sdist_test_data': sdist},
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    packages=find_packages('.', exclude=[
        'tests', 'tests.*', 'tools', 'utils']),
    package_dir={
        'plaso': 'plaso'
    },
    include_package_data=True,
    package_data={
        'plaso': ['*.yaml'],
    },
    zip_safe=False,
    scripts=glob.glob(os.path.join('tools', '*.py')),
    data_files=[
        ('share/plaso/data', glob.glob(
            os.path.join('data', '*'))),
        ('share/doc/plaso', [
            'ACKNOWLEDGEMENTS', 'AUTHORS', 'LICENSE', 'README']),
    ],
)
