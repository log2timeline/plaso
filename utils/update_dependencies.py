#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Script to update the dependencies in various configuration files."""

import os
import sys

# Change PYTHONPATH to include dependencies and projects.
sys.path.insert(0, u'.')

import utils.dependencies  # pylint: disable=wrong-import-position
import utils.projects  # pylint: disable=wrong-import-position


# pylint: disable=redefined-outer-name


class DependencyFileWriter(object):
  """Dependency file writer."""

  def __init__(self, project_definition, dependency_helper):
    """Initializes a dependency file writer.

    Args:
      project_definition (ProjectDefinition): project definition.
      dependency_helper (DependencyHelper): dependency helper.
    """
    super(DependencyFileWriter, self).__init__()
    self._dependency_helper = dependency_helper
    self._project_definition = project_definition


class AppveyorYmlWriter(DependencyFileWriter):
  """Appveyor.yml file writer."""

  _PATH = os.path.join(u'appveyor.yml')

  _VERSION_PYWIN32 = u'220'
  _VERSION_WMI = u'1.4.9'
  _VERSION_SQLITE = u'3180000'

  _DOWNLOAD_PIP = (
      u'  - ps: (new-object net.webclient).DownloadFile('
      u'\'https://bootstrap.pypa.io/get-pip.py\', '
      u'\'C:\\Projects\\get-pip.py\')')

  _DOWNLOAD_PYWIN32 = (
      u'  - ps: (new-object net.webclient).DownloadFile('
      u'\'https://github.com/log2timeline/l2tbinaries/raw/master/win32/'
      u'pywin32-{0:s}.win32-py2.7.exe\', '
      u'\'C:\\Projects\\pywin32-{0:s}.win32-py2.7.exe\')').format(
          _VERSION_PYWIN32)

  _DOWNLOAD_WMI = (
      u'  - ps: (new-object net.webclient).DownloadFile('
      u'\'https://github.com/log2timeline/l2tbinaries/raw/master/win32/'
      u'WMI-{0:s}.win32.exe\', \'C:\\Projects\\WMI-{0:s}.win32.exe\')').format(
          _VERSION_WMI)

  _INSTALL_PIP = (
      u'  - cmd: "%PYTHON%\\\\python.exe C:\\\\Projects\\\\get-pip.py"')

  _INSTALL_PYWIN32 = (
      u'  - cmd: "%PYTHON%\\\\Scripts\\\\easy_install.exe '
      u'C:\\\\Projects\\\\pywin32-{0:s}.win32-py2.7.exe"').format(
          _VERSION_PYWIN32)

  _INSTALL_WMI = (
      u'  - cmd: "%PYTHON%\\\\Scripts\\\\easy_install.exe '
      u'C:\\\\Projects\\\\WMI-{0:s}.win32.exe"').format(_VERSION_WMI)

  _DOWNLOAD_SQLITE = (
      u'  - ps: (new-object net.webclient).DownloadFile('
      u'\'https://www.sqlite.org/2017/sqlite-dll-win32-x86-{0:s}.zip\', '
      u'\'C:\\Projects\\sqlite-dll-win32-x86-{0:s}.zip\')').format(
          _VERSION_SQLITE)

  _EXTRACT_SQLITE = (
      u'  - ps: $Output = Invoke-Expression -Command '
      u'"& \'C:\\\\Program Files\\\\7-Zip\\\\7z.exe\' -y '
      u'-oC:\\\\Projects\\\\ x C:\\\\Projects\\\\'
      u'sqlite-dll-win32-x86-{0:s}.zip 2>&1"').format(_VERSION_SQLITE)

  _INSTALL_SQLITE = (
      u'  - cmd: copy C:\\Projects\\sqlite3.dll C:\\Python27\\DLLs\\')

  _DOWNLOAD_L2TDEVTOOLS = (
      u'  - cmd: git clone https://github.com/log2timeline/l2tdevtools.git && '
      u'move l2tdevtools ..\\')

  _FILE_HEADER = [
      u'environment:',
      u'  matrix:',
      u'    - PYTHON: "C:\\\\Python27"',
      u'',
      u'install:',
      (u'  - cmd: \'"C:\\Program Files\\Microsoft SDKs\\Windows\\v7.1\\Bin\\'
       u'SetEnv.cmd" /x86 /release\''),
      _DOWNLOAD_PIP,
      _DOWNLOAD_PYWIN32,
      _DOWNLOAD_WMI,
      _INSTALL_PIP,
      _INSTALL_PYWIN32,
      _INSTALL_WMI,
      _DOWNLOAD_L2TDEVTOOLS,
      _DOWNLOAD_SQLITE,
      _EXTRACT_SQLITE,
      _INSTALL_SQLITE]

  _L2TDEVTOOLS_UPDATE = (
      u'  - cmd: mkdir dependencies && set PYTHONPATH=..\\l2tdevtools && '
      u'"%PYTHON%\\\\python.exe" ..\\l2tdevtools\\tools\\update.py '
      u'--download-directory dependencies --machine-type x86 '
      u'--msi-targetdir "%PYTHON%" {0:s}')

  _FILE_FOOTER = [
      u'',
      u'build: off',
      u'',
      u'test_script:',
      u'  - "%PYTHON%\\\\python.exe run_tests.py"',
      u'']

  def Write(self):
    """Writes an appveyor.yml file."""
    file_content = []
    file_content.extend(self._FILE_HEADER)

    dependencies = self._dependency_helper.GetL2TBinaries()
    dependencies.extend([u'funcsigs', u'mock', u'pbr'])
    dependencies = u' '.join(dependencies)

    l2tdevtools_update = self._L2TDEVTOOLS_UPDATE.format(dependencies)
    file_content.append(l2tdevtools_update)

    file_content.extend(self._FILE_FOOTER)

    file_content = u'\n'.join(file_content)
    file_content = file_content.encode(u'utf-8')

    with open(self._PATH, 'wb') as file_object:
      file_object.write(file_content)


class DPKGControlWriter(DependencyFileWriter):
  """Dpkg control file writer."""

  _PATH = os.path.join(u'config', u'dpkg', u'control')

  _FILE_CONTENT = u'\n'.join([
      u'Source: {project_name:s}',
      u'Section: python',
      u'Priority: extra',
      u'Maintainer: {maintainer:s}',
      (u'Build-Depends: debhelper (>= 7), python-all (>= 2.7~), '
       u'python-setuptools'),
      u'Standards-Version: 3.9.5',
      u'X-Python-Version: >= 2.7',
      u'Homepage: {homepage_url:s}',
      u'',
      u'Package: {project_name:s}-data',
      u'Architecture: all',
      u'Depends: ${{misc:Depends}}',
      u'Description: Data files for plaso (log2timeline)',
      u'{description_long:s}',
      u'',
      u'Package: python-{project_name:s}',
      u'Architecture: all',
      (u'Depends: {project_name:s}-data, {python2_dependencies:s}'
       u'${{python:Depends}}, ${{misc:Depends}}'),
      u'Description: Python 2 module of plaso (log2timeline)',
      u'{description_long:s}',
      u'',
      u'Package: {project_name:s}-tools',
      u'Architecture: all',
      (u'Depends: python-{project_name:s}, python (>= 2.7~), '
       u'${{python:Depends}}, ${{misc:Depends}}'),
      u'Description: Tools of plaso (log2timeline)',
      u' Plaso (log2timeline) is a framework to create super timelines. Its',
      u' purpose is to extract timestamps from various files found on typical',
      u' computer systems and aggregate them.',
      u''])

  def Write(self):
    """Writes a dpkg control file."""
    dependencies = self._dependency_helper.GetDPKGDepends()

    description_long = self._project_definition.description_long
    description_long = u'\n'.join([
        u' {0:s}'.format(line) for line in description_long.split(u'\n')])

    python2_dependencies = u', '.join(dependencies)
    if python2_dependencies:
      python2_dependencies = u'{0:s}, '.format(python2_dependencies)

    python3_dependencies = u', '.join(dependencies).replace(
        u'python', u'python3')
    if python3_dependencies:
      python3_dependencies = u'{0:s}, '.format(python3_dependencies)

    kwargs = {
        u'description_long': description_long,
        u'description_short': self._project_definition.description_short,
        u'homepage_url': self._project_definition.homepage_url,
        u'maintainer': self._project_definition.maintainer,
        u'project_name': self._project_definition.name,
        u'python2_dependencies': python2_dependencies,
        u'python3_dependencies': python3_dependencies}
    file_content = self._FILE_CONTENT.format(**kwargs)

    file_content = file_content.encode(u'utf-8')

    with open(self._PATH, 'wb') as file_object:
      file_object.write(file_content)


class GIFTCOPRInstallScriptWriter(DependencyFileWriter):
  """Class to help write the gift_copr_install.sh file."""

  _PATH = os.path.join(u'config', u'linux', u'gift_copr_install.sh')

  _FILE_HEADER = [
      u'#!/usr/bin/env bash',
      u'set -e',
      u'',
      u'# Dependencies for running Plaso, alphabetized, one per line.',
      (u'# This should not include packages only required for testing or '
       u'development.')]

  _ADDITIONAL_DEPENDENCIES = [
      u'',
      u'# Additional dependencies for running Plaso tests, alphabetized,',
      u'# one per line.',
      u'TEST_DEPENDENCIES="python-mock";',
      u'',
      u'# Additional dependencies for doing Plaso development, alphabetized,',
      u'# one per line.',
      u'DEVELOPMENT_DEPENDENCIES="python-sphinx',
      u'                          pylint";',
      u'',
      u'# Additional dependencies for doing Plaso debugging, alphabetized,',
      u'# one per line.']

  _FILE_FOOTER = [
      u'',
      u'sudo dnf install dnf-plugins-core',
      u'sudo dnf copr enable @gift/dev',
      u'sudo dnf install -y ${PLASO_DEPENDENCIES}',
      u'',
      u'if [[ "$*" =~ "include-debug" ]]; then',
      u'    sudo dnf install -y ${DEBUG_DEPENDENCIES}',
      u'fi',
      u'',
      u'if [[ "$*" =~ "include-development" ]]; then',
      u'    sudo dnf install -y ${DEVELOPMENT_DEPENDENCIES}',
      u'fi',
      u'',
      u'if [[ "$*" =~ "include-test" ]]; then',
      u'    sudo dnf install -y ${TEST_DEPENDENCIES}',
      u'fi',
      u'']

  def Write(self):
    """Writes a gift_copr_install.sh file."""
    file_content = []
    file_content.extend(self._FILE_HEADER)

    dependencies = self._dependency_helper.GetRPMRequires(exclude_version=True)
    libyal_dependencies = []
    for index, dependency in enumerate(dependencies):
      if index == 0:
        file_content.append(u'PLASO_DEPENDENCIES="{0:s}'.format(dependency))
      elif index + 1 == len(dependencies):
        file_content.append(u'                    {0:s}";'.format(dependency))
      else:
        file_content.append(u'                    {0:s}'.format(dependency))

      if dependency.startswith(u'lib') and dependency.endswith(u'-python'):
        dependency, _, _ = dependency.partition(u'-')
        libyal_dependencies.append(dependency)

    file_content.extend(self._ADDITIONAL_DEPENDENCIES)

    for index, dependency in enumerate(libyal_dependencies):
      if index == 0:
        file_content.append(u'DEBUG_DEPENDENCIES="{0:s}-debuginfo'.format(
            dependency))
      elif index + 1 == len(libyal_dependencies):
        file_content.append(u'                    {0:s}-debuginfo";'.format(
            dependency))
      else:
        file_content.append(u'                    {0:s}-debuginfo'.format(
            dependency))

    file_content.extend(self._FILE_FOOTER)

    file_content = u'\n'.join(file_content)
    file_content = file_content.encode(u'utf-8')

    with open(self._PATH, 'wb') as file_object:
      file_object.write(file_content)


class GIFTPPAInstallScriptWriter(DependencyFileWriter):
  """Class to help write the gift_ppa_install.sh file."""

  _PATH = os.path.join(u'config', u'linux', u'gift_ppa_install.sh')

  _FILE_HEADER = [
      u'#!/usr/bin/env bash',
      u'set -e',
      u'',
      u'# Dependencies for running Plaso, alphabetized, one per line.',
      (u'# This should not include packages only required for testing or '
       u'development.')]

  _ADDITIONAL_DEPENDENCIES = [
      u'',
      u'# Additional dependencies for running Plaso tests, alphabetized,',
      u'# one per line.',
      u'TEST_DEPENDENCIES="python-mock";',
      u'',
      u'# Additional dependencies for doing Plaso development, alphabetized,',
      u'# one per line.',
      u'DEVELOPMENT_DEPENDENCIES="python-sphinx',
      u'                          pylint";',
      u'',
      u'# Additional dependencies for doing Plaso debugging, alphabetized,',
      u'# one per line.']

  _FILE_FOOTER = [
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
    """Writes a gift_ppa_install.sh file."""
    file_content = []
    file_content.extend(self._FILE_HEADER)

    dependencies = self._dependency_helper.GetDPKGDepends(exclude_version=True)
    libyal_dependencies = []
    for index, dependency in enumerate(dependencies):
      if index == 0:
        file_content.append(u'PLASO_DEPENDENCIES="{0:s}'.format(dependency))
      elif index + 1 == len(dependencies):
        file_content.append(u'                    {0:s}";'.format(dependency))
      else:
        file_content.append(u'                    {0:s}'.format(dependency))

      if dependency.startswith(u'lib') and dependency.endswith(u'-python'):
        dependency, _, _ = dependency.partition(u'-')
        libyal_dependencies.append(dependency)

    file_content.extend(self._ADDITIONAL_DEPENDENCIES)

    for index, dependency in enumerate(libyal_dependencies):
      if index == 0:
        file_content.append(u'DEBUG_DEPENDENCIES="{0:s}-dbg'.format(dependency))
      else:
        file_content.append(u'                    {0:s}-dbg'.format(dependency))

      file_content.append(u'                    {0:s}-python-dbg'.format(
          dependency))

    file_content.append(u'                    python-guppy";')

    file_content.extend(self._FILE_FOOTER)

    file_content = u'\n'.join(file_content)
    file_content = file_content.encode(u'utf-8')

    with open(self._PATH, 'wb') as file_object:
      file_object.write(file_content)


class RequirementsWriter(DependencyFileWriter):
  """Requirements.txt file writer."""

  _PATH = u'requirements.txt'

  _FILE_HEADER = [u'pip >= 7.0.0']

  def Write(self):
    """Writes a requirements.txt file."""
    file_content = []
    file_content.extend(self._FILE_HEADER)

    dependencies = self._dependency_helper.GetInstallRequires()
    for dependency in dependencies:
      file_content.append(u'{0:s}'.format(dependency))

    file_content = u'\n'.join(file_content)
    file_content = file_content.encode(u'utf-8')

    with open(self._PATH, 'wb') as file_object:
      file_object.write(file_content)


class SetupCfgWriter(DependencyFileWriter):
  """Setup.cfg file writer."""

  _PATH = u'setup.cfg'

  _FILE_HEADER = u'\n'.join([
      u'[sdist]',
      u'template = MANIFEST.in',
      u'manifest = MANIFEST',
      u'',
      u'[sdist_test_data]',
      u'template = MANIFEST.test_data.in',
      u'manifest = MANIFEST.test_data',
      u'',
      u'[bdist_rpm]',
      u'release = 1',
      u'packager = {maintainer:s}',
      u'doc_files = ACKNOWLEDGEMENTS',
      u'            AUTHORS',
      u'            LICENSE',
      u'            README',
      u'build_requires = python-setuptools'])

  def Write(self):
    """Writes a setup.cfg file."""
    kwargs = {u'maintainer': self._project_definition.maintainer}
    file_header = self._FILE_HEADER.format(**kwargs)

    file_content = [file_header]

    dependencies = self._dependency_helper.GetRPMRequires()
    for index, dependency in enumerate(dependencies):
      if index == 0:
        file_content.append(u'requires = {0:s}'.format(dependency))
      else:
        file_content.append(u'           {0:s}'.format(dependency))

    file_content.append(u'')

    file_content = u'\n'.join(file_content)
    file_content = file_content.encode(u'utf-8')

    with open(self._PATH, 'wb') as file_object:
      file_object.write(file_content)


class TravisBeforeInstallScriptWriter(DependencyFileWriter):
  """Travis-CI install.sh file writer."""

  _PATH = os.path.join(u'config', u'travis', u'install.sh')

  _FILE_HEADER = [
      u'#!/bin/bash',
      u'#',
      u'# Script to set up Travis-CI test VM.',
      u'',
      (u'COVERALL_DEPENDENCIES="python-coverage python-coveralls '
       u'python-docopt";'),
      u'']

  _FILE_FOOTER = [
      u'',
      u'# Exit on error.',
      u'set -e;',
      u'',
      u'if test ${TRAVIS_OS_NAME} = "osx";',
      u'then',
      u'\tgit clone https://github.com/log2timeline/l2tdevtools.git;',
      u'',
      u'\tmv l2tdevtools ../;',
      u'\tmkdir dependencies;',
      u'',
      (u'\tPYTHONPATH=../l2tdevtools ../l2tdevtools/tools/update.py '
       u'--download-directory=dependencies ${L2TBINARIES_DEPENDENCIES} '
       u'${L2TBINARIES_TEST_DEPENDENCIES};'),
      u'',
      u'elif test ${TRAVIS_OS_NAME} = "linux";',
      u'then',
      u'\tsudo rm -f /etc/apt/sources.list.d/travis_ci_zeromq3-source.list;',
      u'',
      u'\tsudo add-apt-repository ppa:gift/dev -y;',
      u'\tsudo apt-get update -q;',
      u'\t# Only install the Python 2 dependencies.',
      (u'\t# Also see: https://docs.travis-ci.com/user/languages/python/'
       u'#Travis-CI-Uses-Isolated-virtualenvs'),
      (u'\tsudo apt-get install -y ${COVERALL_DEPENDENCIES} '
       u'${PYTHON2_DEPENDENCIES} ${PYTHON2_TEST_DEPENDENCIES};'),
      u'fi',
      u'']

  def Write(self):
    """Writes an install.sh file."""
    file_content = []
    file_content.extend(self._FILE_HEADER)

    dependencies = self._dependency_helper.GetL2TBinaries()
    dependencies = u' '.join(dependencies)
    file_content.append(u'L2TBINARIES_DEPENDENCIES="{0:s}";'.format(
        dependencies))

    file_content.append(u'')
    file_content.append(
        u'L2TBINARIES_TEST_DEPENDENCIES="funcsigs mock pbr";')

    file_content.append(u'')

    dependencies = self._dependency_helper.GetDPKGDepends(exclude_version=True)
    dependencies = u' '.join(dependencies)
    file_content.append(u'PYTHON2_DEPENDENCIES="{0:s}";'.format(dependencies))

    file_content.append(u'')
    file_content.append(u'PYTHON2_TEST_DEPENDENCIES="python-mock python-tox";')

    file_content.extend(self._FILE_FOOTER)

    file_content = u'\n'.join(file_content)
    file_content = file_content.encode(u'utf-8')

    with open(self._PATH, 'wb') as file_object:
      file_object.write(file_content)


class ToxIniWriter(DependencyFileWriter):
  """Tox.ini file writer."""

  _PATH = u'tox.ini'

  _FILE_CONTENT = u'\n'.join([
      u'[tox]',
      u'envlist = py2, py3',
      u'',
      u'[testenv]',
      u'pip_pre = True',
      u'setenv =',
      u'    PYTHONPATH = {{toxinidir}}',
      u'deps =',
      u'    coverage',
      u'    mock',
      u'    pytest',
      u'    -rrequirements.txt',
      u'commands =',
      u'    coverage erase',
      (u'    coverage run --source={project_name:s} '
       u'--omit="*_test*,*__init__*,*test_lib*" run_tests.py'),
      u''])

  def Write(self):
    """Writes a setup.cfg file."""
    kwargs = {u'project_name': self._project_definition.name}
    file_content = self._FILE_CONTENT.format(**kwargs)

    file_content = file_content.encode(u'utf-8')

    with open(self._PATH, 'wb') as file_object:
      file_object.write(file_content)


if __name__ == u'__main__':
  project_file = os.path.abspath(__file__)
  project_file = os.path.dirname(project_file)
  project_file = os.path.dirname(project_file)
  project_file = os.path.basename(project_file)
  project_file = u'{0:s}.ini'.format(project_file)

  project_reader = utils.projects.ProjectDefinitionReader()
  with open(project_file, 'rb') as file_object:
    project_definition = project_reader.Read(file_object)

  helper = utils.dependencies.DependencyHelper()

  for writer_class in (
      AppveyorYmlWriter, DPKGControlWriter, GIFTCOPRInstallScriptWriter,
      GIFTPPAInstallScriptWriter, RequirementsWriter, SetupCfgWriter,
      TravisBeforeInstallScriptWriter, ToxIniWriter):
    writer = writer_class(project_definition, helper)
    writer.Write()
