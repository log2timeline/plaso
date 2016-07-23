#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Script to update the dependencies in various configuration files."""

from __future__ import print_function
import sys

# Change PYTHONPATH to include plaso.
sys.path.insert(0, u'.')

import plaso.dependencies


class DPKGControllWriter(object):
  """Class to help write a dpkg control file."""

  _PATH = u'config/dpkg/control'

  _MAINTAINER = (
      u'Log2Timeline developers <log2timeline-dev@googlegroups.com>')

  _FILE_HEADER = [
      u'Source: plaso',
      u'Section: python',
      u'Priority: extra',
      u'Maintainer: {0:s}'.format(_MAINTAINER),
      u'Build-Depends: debhelper (>= 7.0.0), python, python-setuptools',
      u'Standards-Version: 3.9.5',
      u'X-Python-Version: >= 2.7',
      u'Homepage: https://github.com/log2timeline/plaso/',
      u'',
      u'Package: python-plaso',
      u'Architecture: all']

  _FILE_FOOTER = [
      u'Description: Super timeline all the things',
      u' Log2Timeline is a framework to create super timelines. Its purpose',
      u' is to extract timestamps from various files found on typical computer',
      (u' systems and aggregate them. Plaso is the Python rewrite of '
       u'log2timeline.'),
      u'']

  def Write(self):
    """Writes a setup.cfg file."""
    file_content = []
    file_content.extend(self._FILE_HEADER)

    dependencies = plaso.dependencies.GetDPKGDepends()
    dependencies = u', '.join(dependencies)
    file_content.append(
        u'Depends: {0:s}, ${{shlibs:Depends}}, ${{misc:Depends}}'.format(
            dependencies))

    file_content.extend(self._FILE_FOOTER)

    file_content = u'\n'.join(file_content)
    file_content = file_content.encode(u'utf-8')

    with open(self._PATH, 'wb') as file_object:
      file_object.write(file_content)


class SetupCfgWriter(object):
  """Class to help write a setup.cfg file."""

  _PATH = u'setup.cfg'

  _MAINTAINER = (
      u'Log2Timeline developers <log2timeline-dev@googlegroups.com>')

  _FILE_HEADER = [
      u'[bdist_rpm]',
      u'release = 1',
      u'packager = {0:s}'.format(_MAINTAINER),
      u'doc_files = ACKNOWLEDGEMENTS',
      u'            AUTHORS',
      u'            LICENSE',
      u'            README',
      u'build_requires = python-setuptools']

  def Write(self):
    """Writes a setup.cfg file."""
    file_content = []
    file_content.extend(self._FILE_HEADER)

    dependencies = plaso.dependencies.GetRPMRequires()
    for index, dependency in enumerate(dependencies):
      if index == 0:
        file_content.append(u'requires = {0:s}'.format(dependency))
      else:
        file_content.append(u'           {0:s}'.format(dependency))

    file_content = u'\n'.join(file_content)
    file_content = file_content.encode(u'utf-8')

    with open(self._PATH, 'wb') as file_object:
      file_object.write(file_content)

class ToxIniWriter(object):
  """Class to help write a tox.ini file."""

  _PATH = u'tox.ini'

  _FILE_HEADER = [
      u'[tox]',
      u'envlist = py27, py34',
      u'',
      u'[testenv]',
      u'pip_pre = True',
      u'sitepackages = True',
      u'setenv =',
      u'    PYTHONPATH = {toxinidir}',
      u'deps =',
      u'    pip >= 7.0.0',
      u'    pytest',
      u'    mock']

  _FILE_FOOTER = [
      u'commands = python run_tests.py',
      u'']

  def Write(self):
    """Writes a tox.ini file."""
    file_content = []
    file_content.extend(self._FILE_HEADER)

    for dependency in plaso.dependencies.GetInstallRequires():
      file_content.append(u'    {0:s}'.format(dependency))

    file_content.extend(self._FILE_FOOTER)

    file_content = u'\n'.join(file_content)
    file_content = file_content.encode(u'utf-8')

    with open(self._PATH, 'wb') as file_object:
      file_object.write(file_content)


if __name__ == u'__main__':
  # TODO: add support for ./config/linux/install_gift_and_dependencies.sh.

  writer = DPKGControllWriter()
  writer.Write()

  writer = SetupCfgWriter()
  writer.Write()

  writer = ToxIniWriter()
  writer.Write()
