#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Script to update the dependencies in various configuration files."""

import os
import sys

# Change PYTHONPATH to include plaso.
sys.path.insert(0, u'.')

import plaso.dependencies


class DPKGControllWriter(object):
  """Class to help write a dpkg control file."""

  _PATH = os.path.join(u'config', u'dpkg', u'control')

  _MAINTAINER = (
      u'Log2Timeline maintainers <log2timeline-maintainers@googlegroups.com>')

  _FILE_HEADER = [
      u'Source: plaso',
      u'Section: python',
      u'Priority: extra',
      u'Maintainer: {0:s}'.format(_MAINTAINER),
      u'Build-Depends: debhelper (>= 7.0.0), python, python-setuptools',
      u'Standards-Version: 3.9.5',
      u'X-Python-Version: >= 2.7',
      u'Homepage: https://github.com/log2timeline/plaso',
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
    """Writes a dpkg control file."""
    file_content = []
    file_content.extend(self._FILE_HEADER)

    dependencies = plaso.dependencies.GetDPKGDepends()
    dependencies = u', '.join(dependencies)
    file_content.append(
        u'Depends: {0:s}, ${{python:Depends}}, ${{misc:Depends}}'.format(
            dependencies))

    file_content.extend(self._FILE_FOOTER)

    file_content = u'\n'.join(file_content)
    file_content = file_content.encode(u'utf-8')

    with open(self._PATH, 'wb') as file_object:
      file_object.write(file_content)


class GIFTInstallScriptWriter(object):
  """Class to help write the install_gift_and_dependencies.sh file."""

  _PATH = os.path.join(
      u'config', u'linux', u'install_gift_and_dependencies.sh')

  _FILE_HEADER = [
      u'#!/usr/bin/env bash',
      u'set -e',
      u'',
      u'# Dependencies for running Plaso, alphabetized, one per line.',
      (u'# This should not include packages only required for testing or '
       u'development.')]

  _FILE_FOOTER = [
      u'',
      u'# Additional dependencies for running Plaso tests, alphabetized,',
      u'# one per line.',
      u'TEST_DEPENDENCIES="python-mock";',
      u'',
      u'# Additional dependencies for doing Plaso debugging, alphabetized,',
      u'# one per line.',
      u'DEBUG_DEPENDENCIES="python-guppy";',
      u'',
      u'# Additional dependencies for doing Plaso development, alphabetized,',
      u'# one per line.',
      u'DEVELOPMENT_DEPENDENCIES="python-sphinx',
      u'                          pylint";',
      u'',
      u'sudo add-apt-repository ppa:gift/dev -y',
      u'sudo apt-get update -q',
      u'sudo apt-get install -y ${PLASO_DEPENDENCIES}',
      u'',
      u'if [[ "$*" =~ "include-debug" ]]; then',
      u'    sudo apt-get install -y ${DEBUG_DEPENDENCIES}',
      u'fi',
      u'',
      u'if [[ "$*" =~ "include-development" ]]; then',
      u'    sudo apt-get install -y ${DEVELOPMENT_DEPENDENCIES}',
      u'fi',
      u'',
      u'if [[ "$*" =~ "include-test" ]]; then',
      u'    sudo apt-get install -y ${TEST_DEPENDENCIES}',
      u'fi',
      u'']

  def Write(self):
    """Writes a install_gift_and_dependencies.sh file."""
    file_content = []
    file_content.extend(self._FILE_HEADER)

    dependencies = plaso.dependencies.GetDPKGDepends(exclude_version=True)
    for index, dependency in enumerate(dependencies):
      if index == 0:
        file_content.append(u'PLASO_DEPENDENCIES="{0:s}'.format(dependency))
      elif index + 1 == len(dependencies):
        file_content.append(u'                    {0:s}";'.format(dependency))
      else:
        file_content.append(u'                    {0:s}'.format(dependency))

    file_content.extend(self._FILE_FOOTER)

    file_content = u'\n'.join(file_content)
    file_content = file_content.encode(u'utf-8')

    with open(self._PATH, 'wb') as file_object:
      file_object.write(file_content)


class SetupCfgWriter(object):
  """Class to help write a setup.cfg file."""

  _PATH = u'setup.cfg'

  _MAINTAINER = (
      u'Log2Timeline maintainers <log2timeline-maintainers@googlegroups.com>')

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


class TravisBeforeInstallScript(object):
  """Class to help write the Travis-CI before_install.sh file."""

  _PATH = os.path.join(
      u'config', u'travis', u'before_install.sh')

  _FILE_HEADER = [
      u'#!/bin/bash',
      u'#',
      u'# Script to set up Travis-CI test VM.',
      u'',
      (u'COVERALL_DEPENDENCIES="python-coverage python-coveralls '
       u'python-docopt";'),
      u'']

  # TODO: add Python3 dependencies.
  _FILE_FOOTER = [
      u'',
      u'# Exit on error.',
      u'set -e;',
      u'',
      u'if test `uname -s` = "Darwin";',
      u'then',
      u'\tgit clone https://github.com/log2timeline/l2tdevtools.git;',
      u'',
      u'\tmv l2tdevtools ../;',
      u'\tmkdir dependencies;',
      u'',
      (u'\tPYTHONPATH=../l2tdevtools ../l2tdevtools/tools/update.py '
       u'--download-directory=dependencies --preset=plaso;'),
      u'',
      u'elif test `uname -s` = "Linux";',
      u'then',
      u'\tsudo rm -f /etc/apt/sources.list.d/travis_ci_zeromq3-source.list;',
      u'',
      u'\tsudo add-apt-repository ppa:gift/dev -y;',
      u'\tsudo apt-get update -q;',
      (u'\tsudo apt-get install -y ${COVERALL_DEPENDENCIES} '
       u'${PYTHON2_DEPENDENCIES} ${PYTHON2_TEST_DEPENDENCIES};'),
      u'fi',
      u'']

  def Write(self):
    """Writes a setup.cfg file."""
    file_content = []
    file_content.extend(self._FILE_HEADER)

    dependencies = plaso.dependencies.GetDPKGDepends(exclude_version=True)
    dependencies = u' '.join(dependencies)
    file_content.append(u'PYTHON2_DEPENDENCIES="{0:s}";'.format(dependencies))

    file_content.append(u'')

    # TODO: determine test dependencies from plaso.dependencies.
    file_content.append(u'PYTHON2_TEST_DEPENDENCIES="python-mock";')

    file_content.append(u'')

    dependencies = plaso.dependencies.GetDPKGDepends(exclude_version=True)
    dependencies = u' '.join(dependencies)
    dependencies = dependencies.replace(u'python', u'python3')
    file_content.append(u'PYTHON3_DEPENDENCIES="{0:s}";'.format(dependencies))

    file_content.append(u'')

    # TODO: determine test dependencies from plaso.dependencies.
    file_content.append(u'PYTHON3_TEST_DEPENDENCIES="python3-mock";')

    file_content.extend(self._FILE_FOOTER)

    file_content = u'\n'.join(file_content)
    file_content = file_content.encode(u'utf-8')

    with open(self._PATH, 'wb') as file_object:
      file_object.write(file_content)


if __name__ == u'__main__':
  writer = DPKGControllWriter()
  writer.Write()

  writer = GIFTInstallScriptWriter()
  writer.Write()

  writer = SetupCfgWriter()
  writer.Write()

  writer = ToxIniWriter()
  writer.Write()

  writer = TravisBeforeInstallScript()
  writer.Write()
