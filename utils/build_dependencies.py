#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Script to automate creating builds of plaso dependencies."""

import abc
import argparse
import glob
import io
import json
import logging
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import time
import urllib2

try:
  import ConfigParser as configparser
except ImportError:
  import configparser


# TODO: look into merging functionality with update dependencies script.


class DownloadHelper(object):
  """Class that helps in downloading a project."""

  def __init__(self):
    """Initializes the download helper."""
    super(DownloadHelper, self).__init__()
    self._cached_url = u''
    self._cached_page_content = ''

  def Download(self, project_name, project_version):
    """Downloads the project for a given project name and version.

    Args:
      project_name: the name of the project.
      project_version: the version of the project.

    Returns:
      The filename if successful also if the file was already downloaded
      or None on error.
    """
    download_url = self.GetDownloadUrl(project_name, project_version)
    if not download_url:
      logging.warning(u'Unable to determine download URL for: {0:s}'.format(
          project_name))
      return

    return self.DownloadFile(download_url)

  def DownloadFile(self, download_url):
    """Downloads a file from the URL and returns the filename.

       The filename is extracted from the last part of the URL.

    Args:
      download_url: the URL where to download the file.

    Returns:
      The filename if successful also if the file was already downloaded
      or None on error.
    """
    _, _, filename = download_url.rpartition(u'/')

    if not os.path.exists(filename):
      logging.info(u'Downloading: {0:s}'.format(download_url))

      url_object = urllib2.urlopen(download_url)
      if url_object.code != 200:
        return

      file_object = open(filename, 'wb')
      file_object.write(url_object.read())
      file_object.close()

    return filename

  def DownloadPageContent(self, download_url):
    """Downloads the page content from the URL and caches it.

    Args:
      download_url: the URL where to download the page content.

    Returns:
      The page content if successful, None otherwise.
    """
    if not download_url:
      return

    if self._cached_url != download_url:
      url_object = urllib2.urlopen(download_url)

      if url_object.code != 200:
        return

      self._cached_page_content = url_object.read()
      self._cached_url = download_url

    return self._cached_page_content

  @abc.abstractmethod
  def GetDownloadUrl(self, project_name, project_version):
    """Retrieves the download URL for a given project name and version.

    Args:
      project_name: the name of the project.
      project_version: the version of the project.

    Returns:
      The download URL of the project or None on error.
    """

  @abc.abstractmethod
  def GetProjectIdentifier(self, project_name):
    """Retrieves the project identifier for a given project name.

    Args:
      project_name: the name of the project.

    Returns:
      The project identifier or None on error.
    """


class PythonModuleDpkgBuildFilesGenerator(object):
  """Class that helps in generating dpkg build files for Python modules."""

  _PACKAGE_NAMES = {
      u'PyYAML': u'yaml',
      u'pytz': u'tz',
  }

  _EMAIL_ADDRESS = u'Log2Timeline <log2timeline-dev@googlegroups.com>'

  _DOCS_FILENAMES = [
      u'CHANGES', u'CHANGES.txt', u'CHANGES.TXT',
      u'LICENSE', u'LICENSE.txt', u'LICENSE.TXT',
      u'README', u'README.txt', u'README.TXT']

  _CHANGELOG_TEMPLATE = u'\n'.join([
      u'python-{project_name:s} ({project_version!s}-1) unstable; urgency=low',
      u'',
      u'  * Auto-generated',
      u'',
      u' -- {maintainer_email_address:s}  {date_time:s}'])

  _COMPAT_TEMPLATE = u'\n'.join([
      u'7'])

  _CONTROL_TEMPLATE = u'\n'.join([
      u'Source: python-{project_name:s}',
      u'Section: misc',
      u'Priority: extra',
      u'Maintainer: {upstream_maintainer:s}',
      u'Build-Depends: debhelper (>= 7), python, python-setuptools',
      u'Standards-Version: 3.8.3',
      u'Homepage: {upstream_homepage:s}',
      u'',
      u'Package: python-{project_name:s}',
      u'Section: python',
      u'Architecture: all',
      u'Depends: ${{shlibs:Depends}}, ${{python:Depends}}',
      u'Description: {description_short:s}',
      u' {description_long:s}',
      u''])

  _COPYRIGHT_TEMPLATE = u'\n'.join([
      u''])

  _RULES_TEMPLATE = u'\n'.join([
      u'#!/usr/bin/make -f',
      u'# debian/rules that uses debhelper >= 7.',
      u'',
      u'# Uncomment this to turn on verbose mode.',
      u'#export DH_VERBOSE=1',
      u'',
      u'# This has to be exported to make some magic below work.',
      u'export DH_OPTIONS',
      u'',
      u'',
      u'%:',
      u'	dh  $@',
      u'',
      u'override_dh_auto_clean:',
      u'',
      u'override_dh_auto_test:',
      u'',
      u'override_dh_installmenu:',
      u'',
      u'override_dh_installmime:',
      u'',
      u'override_dh_installmodules:',
      u'',
      u'override_dh_installlogcheck:',
      u'',
      u'override_dh_installlogrotate:',
      u'',
      u'override_dh_installpam:',
      u'',
      u'override_dh_installppp:',
      u'',
      u'override_dh_installudev:',
      u'',
      u'override_dh_installwm:',
      u'',
      u'override_dh_installxfonts:',
      u'',
      u'override_dh_gconf:',
      u'',
      u'override_dh_icons:',
      u'',
      u'override_dh_perl:',
      u'',
      u'override_dh_pysupport:',
      u''])

  def __init__(
      self, project_name, project_version, project_information, plaso_path):
    """Initializes the dpkg build files generator.

    Args:
      project_name: the name of the project.
      project_version: the version of the project.
      project_information: a dictionary object containing project information
                           values.
      plaso_path: the path to the plaso source files.
    """
    super(PythonModuleDpkgBuildFilesGenerator, self).__init__()
    self._project_name = project_name
    self._project_version = project_version
    self._project_information = project_information
    self._plaso_path = plaso_path

  def _GenerateChangelogFile(self, dpkg_path):
    """Generate the dpkg build changelog file.

    Args:
      dpkg_path: the path to the dpkg files.
    """
    timezone_minutes, _ = divmod(time.timezone, 60)
    timezone_hours, timezone_minutes = divmod(timezone_minutes, 60)

    # If timezone_hours is -1 {0:02d} will format as -1 instead of -01
    # hence we detect the sign and force a leading zero.
    if timezone_hours < 0:
      timezone_string = u'-{0:02d}{1:02d}'.format(
          -timezone_hours, timezone_minutes)
    else:
      timezone_string = u'+{0:02d}{1:02d}'.format(
          timezone_hours, timezone_minutes)

    date_time_string = u'{0:s} {1:s}'.format(
        time.strftime('%a, %d %b %Y %H:%M:%S'), timezone_string)

    project_name = self._PACKAGE_NAMES.get(
        self._project_name, self._project_name)

    template_values = {
        'project_name': project_name,
        'project_version': self._project_version,
        'maintainer_email_address': self._EMAIL_ADDRESS,
        'date_time': date_time_string}

    filename = os.path.join(dpkg_path, u'changelog')
    with open(filename, 'wb') as file_object:
      data = self._CHANGELOG_TEMPLATE.format(**template_values)
      file_object.write(data.encode('utf-8'))

  def _GenerateCompatFile(self, dpkg_path):
    """Generate the dpkg build compat file.

    Args:
      dpkg_path: the path to the dpkg files.
    """
    filename = os.path.join(dpkg_path, u'compat')
    with open(filename, 'wb') as file_object:
      data = self._COMPAT_TEMPLATE
      file_object.write(data.encode('utf-8'))

  def _GenerateControlFile(self, dpkg_path):
    """Generate the dpkg build control file.

    Args:
      dpkg_path: the path to the dpkg files.
    """
    project_name = self._PACKAGE_NAMES.get(
        self._project_name, self._project_name)

    template_values = {
        'project_name': project_name,
        'upstream_maintainer': self._project_information['upstream_maintainer'],
        'upstream_homepage': self._project_information['upstream_homepage'],
        'description_short': self._project_information['description_short'],
        'description_long': self._project_information['description_long']}

    filename = os.path.join(dpkg_path, u'control')
    with open(filename, 'wb') as file_object:
      data = self._CONTROL_TEMPLATE.format(**template_values)
      file_object.write(data.encode('utf-8'))

  def _GenerateCopyrightFile(self, dpkg_path):
    """Generate the dpkg build copyright file.

    Args:
      dpkg_path: the path to the dpkg files.
    """
    license_file = os.path.join(
        self._plaso_path, u'config', u'licenses',
        u'LICENSE.{0:s}'.format(self._project_name))

    filename = os.path.join(dpkg_path, u'copyright')

    shutil.copy(license_file, filename)

  def _GenerateDocsFile(self, dpkg_path):
    """Generate the dpkg build .docs file.

    Args:
      dpkg_path: the path to the dpkg files.
    """
    project_name = self._PACKAGE_NAMES.get(
        self._project_name, self._project_name)

    # Determine the available doc files.
    doc_files = []
    for filename in self._DOCS_FILENAMES:
      if os.path.exists(filename):
        doc_files.append(filename)

    filename = os.path.join(
        dpkg_path, u'python-{0:s}.docs'.format(project_name))
    with open(filename, 'wb') as file_object:
      file_object.write(u'\n'.join(doc_files))

  def _GenerateRulesFile(self, dpkg_path):
    """Generate the dpkg build rules file.

    Args:
      dpkg_path: the path to the dpkg files.
    """
    filename = os.path.join(dpkg_path, u'rules')
    with open(filename, 'wb') as file_object:
      data = self._RULES_TEMPLATE
      file_object.write(data.encode('utf-8'))

  def GenerateFiles(self, dpkg_path):
    """Generate the dpkg build files.

    Args:
      dpkg_path: the path to the dpkg files.
    """
    os.mkdir(dpkg_path)
    self._GenerateChangelogFile(dpkg_path)
    self._GenerateCompatFile(dpkg_path)
    self._GenerateControlFile(dpkg_path)
    self._GenerateCopyrightFile(dpkg_path)
    self._GenerateDocsFile(dpkg_path)
    self._GenerateRulesFile(dpkg_path)


class GoogleCodeWikiDownloadHelper(DownloadHelper):
  """Class that helps in downloading a wiki-based Google code project."""

  def GetLatestVersion(self, project_name):
    """Retrieves the latest version number for a given project name.

    Args:
      project_name: the name of the project.

    Returns:
      The a string containing the latest version number or None on error.
    """
    download_url = u'https://code.google.com/p/{0:s}/downloads/list'.format(
        project_name)

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return

    # The format of the project download URL is:
    # href="//{project name}.googlecode.com/files/
    # {project name}-{version}.tar.gz
    expression_string = (
        u'href="//{0:s}.googlecode.com/files/'
        u'{0:s}-([0-9]+[.][0-9]+|[0-9]+[.][0-9]+[.][0-9]+)[.]tar[.]gz').format(
            project_name)
    matches = re.findall(expression_string, page_content)

    if not matches:
      return

    # Split the version string and convert every digit into an integer.
    # A string compare of both version strings will yield an incorrect result.
    matches = [map(int, match.split(u'.')) for match in matches]

    # Find the latest version number and transform it back into a string.
    return u'.'.join([u'{0:d}'.format(digit) for digit in max(matches)])

  def GetDownloadUrl(self, project_name, project_version):
    """Retrieves the download URL for a given project name and version.

    Args:
      project_name: the name of the project.
      project_version: the version of the project.

    Returns:
      The download URL of the project or None on error.
    """
    return (
        u'https://{0:s}.googlecode.com/files/{0:s}-{1:s}.tar.gz').format(
            project_name, project_version)

  def GetProjectIdentifier(self, project_name):
    """Retrieves the project identifier for a given project name.

    Args:
      project_name: the name of the project.

    Returns:
      The project identifier or None on error.
    """
    return u'com.google.code.p.{0:s}'.format(project_name)


class GoogleDriveDownloadHelper(DownloadHelper):
  """Class that helps in downloading a Google Drive hosted project."""

  @abc.abstractmethod
  def GetGoogleDriveDownloadsUrl(self, project_name):
    """Retrieves the Google Drive Download URL.

    Args:
      project_name: the name of the project.

    Returns:
      The downloads URL or None on error.
    """

  def GetLatestVersion(self, project_name):
    """Retrieves the latest version number for a given project name.

    Args:
      project_name: the name of the project.

    Returns:
      The latest version number or 0 on error.
    """
    download_url = self.GetGoogleDriveDownloadsUrl(project_name)

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return 0

    # The format of the project download URL is:
    # /host/{random string}/{project name}-{status-}{version}.tar.gz
    # Note that the status is optional and will be: beta, alpha or experimental.
    expression_string = u'/host/[^/]*/{0:s}-[a-z-]*([0-9]+)[.]tar[.]gz'.format(
        project_name)
    matches = re.findall(expression_string, page_content)

    if not matches:
      return 0

    return int(max(matches))

  def GetDownloadUrl(self, project_name, project_version):
    """Retrieves the download URL for a given project name and version.

    Args:
      project_name: the name of the project.
      project_version: the version of the project.

    Returns:
      The download URL of the project or None on error.
    """
    download_url = self.GetGoogleDriveDownloadsUrl(project_name)

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return

    # The format of the project download URL is:
    # /host/{random string}/{project name}-{status-}{version}.tar.gz
    # Note that the status is optional and will be: beta, alpha or experimental.
    expression_string = u'/host/[^/]*/{0:s}-[a-z-]*{1!s}[.]tar[.]gz'.format(
        project_name, project_version)
    matches = re.findall(expression_string, page_content)

    if len(matches) != 1:
      # Try finding a match without the status in case the project provides
      # multiple versions with a different status.
      expression_string = u'/host/[^/]*/{0:s}-{1!s}[.]tar[.]gz'.format(
          project_name, project_version)
      matches = re.findall(expression_string, page_content)

    if not matches or len(matches) != 1:
      return

    return u'https://googledrive.com{0:s}'.format(matches[0])


# pylint: disable=abstract-method
class LibyalGitHubDownloadHelper(GoogleDriveDownloadHelper):
  """Class that helps in downloading a libyal GitHub project."""

  def GetGoogleDriveDownloadsUrl(self, project_name):
    """Retrieves the Download URL from the GitHub project page.

    Args:
      project_name: the name of the project.

    Returns:
      The downloads URL or None on error.
    """
    download_url = (
        u'https://raw.githubusercontent.com/libyal/{0:s}/master/'
        u'{0:s}-wiki.ini').format(project_name)

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return

    config_parser = configparser.RawConfigParser()
    config_parser.readfp(io.BytesIO(page_content))

    return json.loads(config_parser.get('source_package', 'url'))


# pylint: disable=abstract-method
class Log2TimelineGitHubDownloadHelper(GoogleDriveDownloadHelper):
  """Class that helps in downloading a log2timeline GitHub project."""

  def GetGoogleDriveDownloadsUrl(self, project_name):
    """Retrieves the Download URL from the GitHub project page.

    Args:
      project_name: the name of the project.

    Returns:
      The downloads URL or None on error.
    """
    download_url = (
        u'https://github.com/log2timeline/{0:s}/wiki').format(project_name)

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return

    # The format of the project downloads URL is:
    # https://googledrive.com/host/{random string}/
    expression_string = (
        u'<li><a href="(https://googledrive.com/host/[^/]*/)">Downloads</a>'
        u'</li>')
    matches = re.findall(expression_string, page_content)

    if not matches or len(matches) != 1:
      return

    return matches[0]


class PyPiDownloadHelper(DownloadHelper):
  """Class that helps in downloading a pypi code project."""

  def GetLatestVersion(self, project_name):
    """Retrieves the latest version number for a given project name.

    Args:
      project_name: the name of the project.

    Returns:
      The a string containing the latest version number or None on error.
    """
    # TODO: add support to handle index of packages pages, e.g. for pyparsing.
    download_url = u'https://pypi.python.org/pypi/{0:s}'.format(project_name)

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return

    # The format of the project download URL is:
    # https://pypi.python.org/packages/source/{first letter project name}/
    # {project name}/{project name}-{version}.tar.gz
    expression_string = (
        u'https://pypi.python.org/packages/source/{0:s}/{1:s}/'
        u'{1:s}-([0-9]+[.][0-9]+|[0-9]+[.][0-9]+[.][0-9]+)[.]tar[.]gz').format(
            project_name[0], project_name)
    matches = re.findall(expression_string, page_content)

    if not matches:
      return

    # Split the version string and convert every digit into an integer.
    # A string compare of both version strings will yield an incorrect result.
    matches = [map(int, match.split(u'.')) for match in matches]

    # Find the latest version number and transform it back into a string.
    return u'.'.join([u'{0:d}'.format(digit) for digit in max(matches)])

  def GetDownloadUrl(self, project_name, project_version):
    """Retrieves the download URL for a given project name and version.

    Args:
      project_name: the name of the project.
      project_version: the version of the project.

    Returns:
      The download URL of the project or None on error.
    """
    return (
        u'https://pypi.python.org/packages/source/{0:s}/{1:s}/'
        u'{1:s}-{2:s}.tar.gz').format(
            project_name[0], project_name, project_version)

  def GetProjectIdentifier(self, project_name):
    """Retrieves the project identifier for a given project name.

    Args:
      project_name: the name of the project.

    Returns:
      The project identifier or None on error.
    """
    return u'org.python.pypi.{0:s}'.format(project_name)


class SourceForgeDownloadHelper(DownloadHelper):
  """Class that helps in downloading a Source Forge project."""

  def GetLatestVersion(self, project_name):
    """Retrieves the latest version number for a given project name.

    Args:
      project_name: the name of the project.

    Returns:
      The a string containing the latest version number or None on error.
    """
    # TODO: make this more robust to detect different naming schemes.
    download_url = 'http://sourceforge.net/projects/{0:s}/files/{0:s}/'.format(
        project_name)

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return 0

    # The format of the project download URL is:
    # /projects/{project name}/files/{project name}/{project name}-{version}/
    expression_string = (
        '<a href="/projects/{0:s}/files/{0:s}/'
        '{0:s}-([0-9]+[.][0-9]+[.][0-9]+)/"').format(project_name)
    matches = re.findall(expression_string, page_content)

    if not matches:
      return 0

    numeric_matches = [''.join(match.split('.')) for match in matches]
    return matches[numeric_matches.index(max(numeric_matches))]

  def GetDownloadUrl(self, project_name, project_version):
    """Retrieves the download URL for a given project name and version.

    Args:
      project_name: the name of the project.
      project_version: the version of the project.

    Returns:
      The download URL of the project or None on error.
    """
    download_url = (
        'http://downloads.sourceforge.net/project/{0:s}/{0:s}/{0:s}-{1:s}'
        '/{0:s}-{1:s}.tar.gz').format(project_name, project_version)

    return self.DownloadFile(download_url)

  def GetProjectIdentifier(self, project_name):
    """Retrieves the project identifier for a given project name.

    Args:
      project_name: the name of the project.

    Returns:
      The project identifier or None on error.
    """
    return u'net.sourceforge.projects.{0:s}'.format(project_name)


class BuildHelper(object):
  """Base class that helps in building."""

  LOG_FILENAME = u'build.log'
  ENCODING = 'utf-8'

  def Extract(self, source_filename):
    """Extracts the given source filename.

    Args:
      source_filename: the name of the source package file.

    Returns:
      The name of the directory the files were extracted to if successful
      or None on error.
    """
    if not source_filename or not os.path.exists(source_filename):
      return

    archive = tarfile.open(source_filename, 'r:gz', encoding=self.ENCODING)
    directory_name = ''

    for tar_info in archive.getmembers():
      filename = getattr(tar_info, 'name', None)
      try:
        filename = filename.decode(self.ENCODING)
      except UnicodeDecodeError:
        logging.warning(
            u'Unable to decode filename in tar file: {0:s}'.format(
                source_filename))
        continue

      if filename is None:
        logging.warning(
            u'Missing filename in tar file: {0:s}'.format(source_filename))
        continue

      if not directory_name:
        # Note that this will set directory name to an empty string
        # if filename start with a /.
        directory_name, _, _ = filename.partition(u'/')
        if not directory_name or directory_name.startswith(u'..'):
          logging.error(
              u'Unsuppored directory name in tar file: {0:s}'.format(
                  source_filename))
          return
        if os.path.exists(directory_name):
          break
        logging.info(u'Extracting: {0:s}'.format(source_filename))

      elif not filename.startswith(directory_name):
        logging.warning(
            u'Skipping: {0:s} in tar file: {1:s}'.format(
                filename, source_filename))
        continue

      archive.extract(tar_info)
    archive.close()

    return directory_name


class DpkgBuildHelper(BuildHelper):
  """Class that helps in building dpkg packages (.deb)."""

  # TODO: determine BUILD_DEPENDENCIES from the build files?
  # TODO: what about flex, byacc?
  _BUILD_DEPENDENCIES = frozenset([
      'git',
      'build-essential',
      'autotools-dev',
      'autoconf',
      'automake',
      'autopoint',
      'libtool',
      'gettext',
      'debhelper',
      'fakeroot',
      'quilt',
      'zlib1g-dev',
      'libbz2-dev',
      'libssl-dev',
      'libfuse-dev',
      'python-dev',
      'python-setuptools',
      'libsqlite3-dev',
  ])

  def _BuildPrepare(self, source_directory):
    """Make the necassary preperations before building the dpkg packages.

    Args:
      source_directory: the name of the source directory.

    Returns:
      True if the preparations were successful, False otherwise.
    """
    # Script to run before building, e.g. to change the dpkg build files.
    if os.path.exists(u'prep-dpkg.sh'):
      command = u'sh ../prep-dpkg.sh'
      exit_code = subprocess.call(
          u'(cd {0:s} && {1:s})'.format(source_directory, command), shell=True)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        return False

    return True

  def _BuildFinalize(self, source_directory):
    """Make the necassary finalizations after building the dpkg packages.

    Args:
      source_directory: the name of the source directory.

    Returns:
      True if the finalizations were successful, False otherwise.
    """
    # Script to run after building, e.g. to automatically upload
    # the dpkg package files to an apt repository.
    if os.path.exists(u'post-dpkg.sh'):
      command = u'sh ../post-dpkg.sh'
      exit_code = subprocess.call(
          u'(cd {0:s} && {1:s})'.format(source_directory, command), shell=True)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        return False

    return True

  @classmethod
  def CheckBuildDependencies(cls):
    """Checks if the build dependencies are met.

    Returns:
      A list of package names that need to be installed or an empty list.
    """
    missing_packages = []
    for package_name in cls._BUILD_DEPENDENCIES:
      if not cls.CheckIsInstalled(package_name):
        missing_packages.append(package_name)

    return missing_packages

  @classmethod
  def CheckIsInstalled(cls, package_name):
    """Checks if a package is installed.

    Args:
      package_name: the name of the package.

    Returns:
      A boolean value containing true if the package is installed
      false otherwise.
    """
    command = u'dpkg-query -l {0:s} >/dev/null 2>&1'.format(package_name)
    exit_code = subprocess.call(command, shell=True)
    return exit_code == 0


class LibyalDpkgBuildHelper(DpkgBuildHelper):
  """Class that helps in building libyal dpkg packages (.deb)."""

  def __init__(self):
    """Initializes the build helper."""
    super(LibyalDpkgBuildHelper, self).__init__()
    self.architecture = platform.machine()

    if self.architecture == 'i686':
      self.architecture = 'i386'
    elif self.architecture == 'x86_64':
      self.architecture = 'amd64'

  def Build(self, source_filename):
    """Builds the dpkg packages.

    Args:
      source_filename: the name of the source package file.

    Returns:
      True if the build was successful, False otherwise.
    """
    source_directory = self.Extract(source_filename)
    if not source_directory:
      logging.error(
          u'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    dpkg_directory = os.path.join(source_directory, u'dpkg')
    if not os.path.exists(dpkg_directory):
      dpkg_directory = os.path.join(source_directory, u'config', u'dpkg')

    if not os.path.exists(dpkg_directory):
      logging.error(u'Missing dpkg sub directory in: {0:s}'.format(
          source_directory))
      return False

    debian_directory = os.path.join(source_directory, u'debian')

    # If there is a debian directory remove it and recreate it from
    # the dpkg directory.
    if os.path.exists(debian_directory):
      logging.info(u'Removing: {0:s}'.format(debian_directory))
      shutil.rmtree(debian_directory)
    shutil.copytree(dpkg_directory, debian_directory)

    if not self._BuildPrepare(source_directory):
      return False

    command = u'dpkg-buildpackage -uc -us -rfakeroot > {0:s} 2>&1'.format(
        os.path.join(u'..', self.LOG_FILENAME))
    exit_code = subprocess.call(
        u'(cd {0:s} && {1:s})'.format(source_directory, command), shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    if not self._BuildFinalize(source_directory):
      return False

    return True

  def Clean(self, library_name, library_version):
    """Cleans the dpkg packages in the current directory.

    Args:
      library_name: the name of the library.
      library_version: the version of the library.
    """
    filenames_to_ignore = re.compile(
        u'^{0:s}[-_].*{1!s}'.format(library_name, library_version))

    # Remove files of previous versions in the format:
    # library[-_]version-1_architecture.*
    filenames = glob.glob(
        u'{0:s}[-_]*[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]-1_'
        u'{1:s}.*'.format(library_name, self.architecture))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

    # Remove files of previous versions in the format:
    # library[-_]*version-1.*
    filenames = glob.glob(
        u'{0:s}[-_]*[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]-1.*'.format(
            library_name))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

  def GetOutputFilename(self, library_name, library_version):
    """Retrieves the filename of one of the resulting files.

    Args:
      library_name: the name of the library.
      library_version: the version of the library.

    Returns:
      A filename of one of the resulting dpkg packages.
    """
    return u'{0:s}_{1!s}-1_{2:s}.deb'.format(
        library_name, library_version, self.architecture)


class PythonModuleDpkgBuildHelper(DpkgBuildHelper):
  """Class that helps in building python module dpkg packages (.deb)."""

  _PACKAGE_NAMES = {
      u'PyYAML': u'yaml',
      u'pytz': u'tz',
  }

  def Build(
      self, source_filename, project_name, project_version,
      project_information, plaso_path):
    """Builds the dpkg packages.

    Args:
      source_filename: the name of the source package file.
      project_name: the name of the project.
      project_version: the version of the project.
      project_information: a dictionary object containing project information
                           values.
      plaso_path: the path to the plaso source files.

    Returns:
      True if the build was successful, False otherwise.
    """
    source_directory = self.Extract(source_filename)
    if not source_directory:
      logging.error(
          u'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    dpkg_directory = os.path.join(source_directory, u'dpkg')
    if not os.path.exists(dpkg_directory):
      dpkg_directory = os.path.join(source_directory, u'config', u'dpkg')

    if not os.path.exists(dpkg_directory):
      # Generate the dpkg build files if necessary.
      os.chdir(source_directory)

      build_files_generator = PythonModuleDpkgBuildFilesGenerator(
          project_name, project_version, project_information, plaso_path)
      build_files_generator.GenerateFiles(u'dpkg')

      os.chdir(u'..')

      dpkg_directory = os.path.join(source_directory, u'dpkg')

    if not os.path.exists(dpkg_directory):
      logging.error(u'Missing dpkg sub directory in: {0:s}'.format(
          source_directory))
      return False

    debian_directory = os.path.join(source_directory, u'debian')

    # If there is a debian directory remove it and recreate it from
    # the dpkg directory.
    if os.path.exists(debian_directory):
      logging.info(u'Removing: {0:s}'.format(debian_directory))
      shutil.rmtree(debian_directory)
    shutil.copytree(dpkg_directory, debian_directory)

    if not self._BuildPrepare(source_directory):
      return False

    command = u'dpkg-buildpackage -uc -us -rfakeroot > {0:s} 2>&1'.format(
        os.path.join(u'..', self.LOG_FILENAME))
    exit_code = subprocess.call(
        u'(cd {0:s} && {1:s})'.format(source_directory, command), shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    if not self._BuildFinalize(source_directory):
      return False

    return True

  def Clean(self, project_name, project_version):
    """Cleans the dpkg packages in the current directory.

    Args:
      project_name: the name of the project.
      project_version: the version of the project.
    """
    filenames_to_ignore = re.compile(
        u'^python-{0:s}[-_].*{1!s}'.format(project_name, project_version))

    # Remove files of previous versions in the format:
    # python-{project name}[-_]{project version}-1_architecture.*
    filenames = glob.glob(
        u'python-{0:s}[-_]*-1_all.*'.format(project_name))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

    # Remove files of previous versions in the format:
    # python-{project name}[-_]*version-1.*
    filenames = glob.glob(
        u'python-{0:s}[-_]*-1.*'.format(project_name))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

  def GetOutputFilename(self, project_name, project_version):
    """Retrieves the filename of one of the resulting files.

    Args:
      project_name: the name of the project.
      project_version: the version of the project.

    Returns:
      A filename of one of the resulting dpkg packages.
    """
    project_name = self._PACKAGE_NAMES.get(project_name, project_name)

    return u'python-{0:s}_{1!s}-1_all.deb'.format(project_name, project_version)


class MsiBuildHelper(BuildHelper):
  """Class that helps in building Microsoft Installer packages (.msi)."""
  # TODO: implement.


class PkgBuildHelper(BuildHelper):
  """Class that helps in building MacOS-X packages (.pkg)."""

  def __init__(self):
    """Initializes the build helper."""
    super(PkgBuildHelper, self).__init__()
    self._pkgbuild = os.path.join(u'/', u'usr', u'bin', u'pkgbuild')

  def _BuildDmg(self, pkg_filename, dmg_filename):
    """Builds the distributable disk image (.dmg) from the pkg.

    Args:
      pkg_filename: the name of the pkg file (which is technically
                    a directory).
      dmg_filename: the name of the dmg file.

    Returns:
      True if the build was successful, False otherwise.
    """
    command = (
        u'hdiutil create {0:s} -srcfolder {1:s} -fs HFS+').format(
            dmg_filename, pkg_filename)
    exit_code = subprocess.call(command, shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    return True

  def _BuildPkg(
      self, source_directory, project_identifier, project_version,
      pkg_filename):
    """Builds the distributable disk image (.dmg) from the pkg.

    Args:
      source_directory: the name of the source directory.
      project_identifier: the project identifier.
      project_version: the version of the project.
      pkg_filename: the name of the pkg file (which is technically
                    a directory).

    Returns:
      True if the build was successful, False otherwise.
    """
    command = (
        u'{0:s} --root {1:s}/tmp/ --identifier {2:s} '
        u'--version {3!s} --ownership recommended {4:s}').format(
            self._pkgbuild, source_directory, project_identifier,
            project_version, pkg_filename)
    exit_code = subprocess.call(command, shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    return True

  def Clean(self, project_name, project_version):
    """Cleans the MacOS-X packages in the current directory.

    Args:
      project_name: the name of the project.
      project_version: the version of the project.
    """
    filenames_to_ignore = re.compile(
        u'^{0:s}-.*{1!s}'.format(project_name, project_version))

    # Remove files of previous versions in the format:
    # project-*version.dmg
    filenames = glob.glob(u'{0:s}-*.dmg'.format(project_name))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

    # Remove files of previous versions in the format:
    # project-*version.pkg
    filenames = glob.glob(u'{0:s}-*.pkg'.format(project_name))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        shutil.rmtree(filename)

  def GetOutputFilename(self, project_name, project_version):
    """Retrieves the filename of one of the resulting files.

    Args:
      project_name: the name of the project.
      project_version: the version of the project.

    Returns:
      A filename of one of the resulting rpms.
    """
    return u'{0:s}-{1!s}.dmg'.format(project_name, project_version)


class LibyalPkgBuildHelper(PkgBuildHelper):
  """Class that helps in building MacOS-X packages (.pkg)."""

  def Build(self, source_filename, library_name, library_version):
    """Builds the pkg package and distributable disk image (.dmg).

    Args:
      source_filename: the name of the source package file.
      library_name: the name of the library.
      library_version: the version of the library.

    Returns:
      True if the build was successful, False otherwise.
    """
    source_directory = self.Extract(source_filename)
    if not source_directory:
      logging.error(
          u'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    dmg_filename = u'{0:s}.dmg'.format(source_directory)
    pkg_filename = u'{0:s}.pkg'.format(source_directory)
    log_filename = os.path.join(u'..', self.LOG_FILENAME)

    sdks_path = os.path.join(
        u'/', u'Applications', u'Xcode.app', u'Contents', u'Developer',
        u'Platforms', u'MacOSX.platform', u'Developer', u'SDKs')

    for sub_path in [u'MacOSX10.7.sdk', u'MacOSX10.8.sdk', u'MacOSX10.9.sdk']:
      sdk_path = os.path.join(sdks_path, sub_path)
      if os.path.isdir(sub_path):
        break

    if sdk_path:
      cflags = u'CFLAGS="-isysroot {0:s}"'.format(sdk_path)
      ldflags = u'LDFLAGS="-Wl,-syslibroot,{0:s}"'.format(sdk_path)
    else:
      cflags = u''
      ldflags = u''

    if not os.path.exists(pkg_filename):
      if cflags and ldflags:
        command = (
            u'{0:s} {1:s} ./configure --prefix=/usr --enable-python '
            u'--with-pyprefix --disable-dependency-tracking > {2:s} '
            u'2>&1').format(cflags, ldflags, log_filename)
      else:
        command = (
            u'./configure --prefix=/usr --enable-python --with-pyprefix '
            u'> {0:s} 2>&1').format(log_filename)

      exit_code = subprocess.call(
          u'(cd {0:s} && {1:s})'.format(source_directory, command), shell=True)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        return False

      command = u'make >> {0:s} 2>&1'.format(log_filename)
      exit_code = subprocess.call(
          u'(cd {0:s} && {1:s})'.format(source_directory, command), shell=True)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        return False

      command = u'make install DESTDIR={0:s}/tmp >> {1:s} 2>&1'.format(
          os.path.abspath(source_directory), log_filename)
      exit_code = subprocess.call(
          u'(cd {0:s} && {1:s})'.format(source_directory, command), shell=True)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        return False

      share_doc_path = os.path.join(
          source_directory, u'tmp', u'usr', u'share', u'doc', library_name)
      if not os.path.exists(share_doc_path):
        os.makedirs(share_doc_path)

      shutil.copy(os.path.join(source_directory, u'AUTHORS'), share_doc_path)
      shutil.copy(os.path.join(source_directory, u'COPYING'), share_doc_path)
      shutil.copy(os.path.join(source_directory, u'NEWS'), share_doc_path)
      shutil.copy(os.path.join(source_directory, u'README'), share_doc_path)

      project_identifier = u'com.google.code.p.{0:s}'.format(library_name)
      if not self._BuildPkg(
          source_directory, project_identifier, library_version, pkg_filename):
        return False

    if not self._BuildDmg(pkg_filename, dmg_filename):
      return False

    return True


class PythonModulePkgBuildHelper(PkgBuildHelper):
  """Class that helps in building MacOS-X packages (.pkg)."""

  def Build(
      self, source_filename, unused_project_name, project_version,
      project_identifier):
    """Builds the pkg.

    Args:
      source_filename: the name of the source package file.
      project_name: the name of the project.
      project_version: the version of the project.
      project_identifier: the project identifier.

    Returns:
      True if the build was successful, False otherwise.
    """
    source_directory = self.Extract(source_filename)
    if not source_directory:
      logging.error(
          u'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    dmg_filename = u'{0:s}.dmg'.format(source_directory)
    pkg_filename = u'{0:s}.pkg'.format(source_directory)

    if not os.path.exists(pkg_filename):
      command = u'python setup.py build > {0:s} 2>&1'.format(
          os.path.join(u'..', self.LOG_FILENAME))
      exit_code = subprocess.call(
          u'(cd {0:s} && {1:s})'.format(source_directory, command), shell=True)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        return False

      command = u'python setup.py install --root={0:s}/tmp > {1:s} 2>&1'.format(
          os.path.abspath(source_directory),
          os.path.join(u'..', self.LOG_FILENAME))
      exit_code = subprocess.call(
          u'(cd {0:s} && {1:s})'.format(source_directory, command), shell=True)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        return False

      # Copy the license file to the egg-info sub directory.
      for license_file in [
          u'COPYING', u'LICENSE', u'LICENSE.TXT', u'LICENSE.txt']:
        if not os.path.exists(os.path.join(source_directory, license_file)):
          continue

        command = (
            u'find ./tmp -type d -name \\*.egg-info -exec cp {0:s} {{}} '
            u'\\;').format(license_file)
        exit_code = subprocess.call(
            u'(cd {0:s} && {1:s})'.format(source_directory, command),
            shell=True)
        if exit_code != 0:
          logging.error(u'Running: "{0:s}" failed.'.format(command))
          return False

      if not self._BuildPkg(
          source_directory, project_identifier, project_version, pkg_filename):
        return False

    if not self._BuildDmg(pkg_filename, dmg_filename):
      return False

    return True


class RpmBuildHelper(BuildHelper):
  """Class that helps in building rpm packages (.rpm)."""

  # TODO: determine BUILD_DEPENDENCIES from the build files?
  _BUILD_DEPENDENCIES = frozenset([
      'git',
      'binutils',
      'autoconf',
      'automake',
      'libtool',
      'gettext-devel',
      'make',
      'pkgconfig',
      'gcc',
      'gcc-c++',
      'flex',
      'byacc',
      'zlib-devel',
      'bzip2-devel',
      'openssl-devel',
      'fuse-devel',
      'rpm-build',
      'python-devel',
      'git',
      'python-dateutil',
      'python-setuptools',
      'sqlite-devel',
  ])

  def __init__(self):
    """Initializes the build helper."""
    super(RpmBuildHelper, self).__init__()
    self.architecture = platform.machine()

    self.rpmbuild_path = os.path.join(u'~', u'rpmbuild')
    self.rpmbuild_path = os.path.expanduser(self.rpmbuild_path)

    self._rpmbuild_rpms_path = os.path.join(
        self.rpmbuild_path, u'RPMS', self.architecture)
    self._rpmbuild_sources_path = os.path.join(self.rpmbuild_path, u'SOURCES')
    self._rpmbuild_specs_path = os.path.join(self.rpmbuild_path, u'SPECS')

  def _BuildFromSpecFile(self, spec_filename):
    """Builds the rpms directly from a spec file.

    Args:
      spec_filename: the name of the spec file as stored in the rpmbuild
                     SPECS sub directory.

    Returns:
      True if the build was successful, False otherwise.
    """
    current_path = os.getcwd()
    os.chdir(self.rpmbuild_path)

    command = u'rpmbuild -ba {0:s} > {1:s} 2>&1'.format(
        os.path.join(u'SPECS', spec_filename), self.LOG_FILENAME)
    exit_code = subprocess.call(command, shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))

    os.chdir(current_path)

    return exit_code == 0

  def _BuildFromSourcePackage(self, source_filename):
    """Builds the rpms directly from the source package file.

    For this to work the source package needs to contain a valid rpm .spec file.

    Args:
      source_filename: the name of the source package file.

    Returns:
      True if the build was successful, False otherwise.
    """
    command = u'rpmbuild -ta {0:s} > {1:s} 2>&1'.format(
        source_filename, self.LOG_FILENAME)
    exit_code = subprocess.call(command, shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    return True

  def _CreateRpmbuildDirectories(self):
    """Creates the rpmbuild and sub directories."""
    if not os.path.exists(self.rpmbuild_path):
      os.mkdir(self.rpmbuild_path)

    if not os.path.exists(self._rpmbuild_sources_path):
      os.mkdir(self._rpmbuild_sources_path)

    if not os.path.exists(self._rpmbuild_specs_path):
      os.mkdir(self._rpmbuild_specs_path)

  def _CreateSpecFile(self, project_name, spec_file_data):
    """Creates a spec file in the rpmbuild directory.

    Args:
      project_name: the name of the project.
      spec_file_data: the spec file data.
    """
    spec_filename = os.path.join(
        self._rpmbuild_specs_path, u'{0:s}.spec'.format(project_name))

    spec_file = open(spec_filename, 'w')
    spec_file.write(spec_file_data)
    spec_file.close()

  def _CopySourceFile(self, source_filename):
    """Copies the source file to the rpmbuild directory.

    Args:
      source_filename: the name of the source package file.
    """
    shutil.copy(source_filename, self._rpmbuild_sources_path)

  def _MoveRpms(self, project_name, project_version):
    """Moves the rpms from the rpmbuild directory into to current directory.

    Args:
      project_name: the name of the project.
      project_version: the version of the project.
    """
    filenames = glob.glob(os.path.join(
        self._rpmbuild_rpms_path, u'{0:s}-*{1!s}-1.{2:s}.rpm'.format(
            project_name, project_version, self.architecture)))
    for filename in filenames:
      logging.info(u'Moving: {0:s}'.format(filename))
      shutil.move(filename, '.')

  @classmethod
  def CheckBuildDependencies(cls):
    """Checks if the build dependencies are met.

    Returns:
      A list of package names that need to be installed or an empty list.
    """
    missing_packages = []
    for package_name in cls._BUILD_DEPENDENCIES:
      if not cls.CheckIsInstalled(package_name):
        missing_packages.append(package_name)

    return missing_packages

  @classmethod
  def CheckIsInstalled(cls, package_name):
    """Checks if a package is installed.

    Args:
      package_name: the name of the package.

    Returns:
      A boolean value containing true if the package is installed
      false otherwise.
    """
    command = u'rpm -qi {0:s} >/dev/null 2>&1'.format(package_name)
    exit_code = subprocess.call(command, shell=True)
    return exit_code == 0

  def Clean(self, project_name, project_version):
    """Cleans the rpmbuild directory.

    Args:
      project_name: the name of the project.
      project_version: the version of the project.
    """
    # Remove previous versions build directories.
    filenames_to_ignore = re.compile(
        u'{0:s}-{1!s}'.format(project_name, project_version))

    filenames = glob.glob(os.path.join(
        self.rpmbuild_path, u'BUILD', u'{0:s}-*'.format(project_name)))
    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        shutil.rmtree(filename)

    # Remove previous versions of rpms.
    filenames_to_ignore = re.compile(
        u'{0:s}-.*{1!s}-1.{2:s}.rpm'.format(
            project_name, project_version, self.architecture))

    rpm_filenames_glob = u'{0:s}-*-1.{1:s}.rpm'.format(
        project_name, self.architecture)

    filenames = glob.glob(rpm_filenames_glob)
    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

    filenames = glob.glob(os.path.join(
        self.rpmbuild_path, u'RPMS', self.architecture, rpm_filenames_glob))
    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

    # Remove previous versions of source rpms.
    filenames_to_ignore = re.compile(
        u'{0:s}-.*{1!s}-1.src.rpm'.format(project_name, project_version))

    filenames = glob.glob(os.path.join(
        self.rpmbuild_path, u'SRPMS',
        u'{0:s}-*-1.src.rpm'.format(project_name)))
    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

  def GetOutputFilename(self, project_name, project_version):
    """Retrieves the filename of one of the resulting files.

    Args:
      project_name: the name of the project.
      project_version: the version of the project.

    Returns:
      A filename of one of the resulting rpms.
    """
    return u'{0:s}-{1!s}-1.{2:s}.rpm'.format(
        project_name, project_version, self.architecture)


class LibyalRpmBuildHelper(RpmBuildHelper):
  """Class that helps in building libyal rpm packages (.rpm)."""

  def Build(self, source_filename, library_name, library_version):
    """Builds the rpms.

    Args:
      source_filename: the name of the source package file.
      library_name: the name of the library.
      library_version: the version of the library.

    Returns:
      True if the build was successful, False otherwise.
    """
    if not self._BuildFromSourcePackage(source_filename):
      return False

    # Move the rpms to the build directory.
    self._MoveRpms(library_name, library_version)

    # TODO: clean up rpmbuilds directory after move.

    return True


class PythonModuleRpmBuildHelper(RpmBuildHelper):
  """Class that helps in building rpm packages (.rpm)."""

  def __init__(self):
    """Initializes the build helper."""
    super(PythonModuleRpmBuildHelper, self).__init__()
    self.architecture = 'noarch'

  def Build(self, source_filename, project_name, project_version):
    """Builds the rpms.

    Args:
      source_filename: the name of the source package file.
      project_name: the name of the project.
      project_version: the version of the project.

    Returns:
      True if the build was successful, False otherwise.
    """
    source_directory = self.Extract(source_filename)
    if not source_directory:
      logging.error(
          u'Extraction of source package: {0:s} failed'.format(source_filename))
      return False

    command = u'python setup.py bdist_rpm > {0:s} 2>&1'.format(
        os.path.join(u'..', self.LOG_FILENAME))
    exit_code = subprocess.call(
        u'(cd {0:s} && {1:s})'.format(source_directory, command), shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    # Move the rpms to the build directory.
    filenames = glob.glob(os.path.join(
        source_directory, u'dist', u'{0:s}-{1!s}-1.{2:s}.rpm'.format(
            project_name, project_version, self.architecture)))
    for filename in filenames:
      logging.info(u'Moving: {0:s}'.format(filename))
      shutil.move(filename, '.')

    return True

  def Clean(self, project_name, project_version):
    """Cleans the rpmbuild directory.

    Args:
      project_name: the name of the project.
      project_version: the version of the project.
    """
    # Remove previous versions build directories.
    for filename in [u'build', u'dist']:
      if os.path.exists(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        shutil.rmtree(filename, True)

    # Remove previous versions of rpms.
    filenames_to_ignore = re.compile(u'{0:s}-.*{1!s}-1.{2:s}.rpm'.format(
            project_name, project_version, self.architecture))

    rpm_filenames_glob = u'{0:s}-*-1.{1:s}.rpm'.format(
        project_name, self.architecture)

    filenames = glob.glob(rpm_filenames_glob)
    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)


class DependencyBuilder(object):
  """Class that helps in building dependencies."""

  _LIBYAL_LIBRARIES = frozenset([
      'libbde', 'libesedb', 'libevt', 'libevtx', 'libewf', 'libfwsi', 'liblnk',
      'libmsiecf', 'libolecf', 'libqcow', 'libregf', 'libsmdev', 'libsmraw',
      'libvhdi', 'libvmdk', 'libvshadow'])

  _PATCHES_URL = (
    u'https://googledrive.com/host/0B30H7z4S52FleW5vUHBnblJfcjg/'
    u'3rd%20party/patches')

  _PYTHON_MODULES = frozenset([
    'bencode', 'binplist', 'construct', 'dfvfs', 'dpkt', 'pyparsing',
    'pysqlite', 'pytz', 'PyYAML', 'six'])

  PROJECT_TYPE_GOOGLE_CODE_WIKI = 1
  PROJECT_TYPE_PYPI = 2
  PROJECT_TYPE_SOURCE_FORGE = 3
  PROJECT_TYPE_GITHUB_LIBYAL = 4
  PROJECT_TYPE_GITHUB_LOG2TIMELINE = 5

  def __init__(self, build_target, plaso_path):
    """Initializes the dependency builder.

    Args:
      build_target: the build target.
      plaso_path: the path to the plaso source files.
    """
    super(DependencyBuilder, self).__init__()
    self._build_target = build_target
    self._plaso_path = plaso_path

  def _BuildDependency(
      self, download_helper, project_name, project_information):
    """Builds a dependency.

    Args:
      download_helper: the download helper (instance of DownloadHelper).
      project_name: the name of the project
      project_information: a dictionary object containing project information
                           values.

    Returns:
      True if the build is successful or False on error.
    """
    project_version = download_helper.GetLatestVersion(project_name)
    if not project_version:
      logging.error(
          u'Unable to determine latest version of: {0:s}'.format(project_name))
      return False

    source_filename = download_helper.Download(project_name, project_version)
    if source_filename:
      filenames_to_ignore = re.compile(u'^{0:s}-.*{1!s}'.format(
          project_name, project_version))

      # Remove files of previous versions in the format:
      # {project name}-*.tar.gz
      filenames = glob.glob(u'{0:s}-*.tar.gz'.format(project_name))
      for filename in filenames:
        if not filenames_to_ignore.match(filename):
          logging.info(u'Removing: {0:s}'.format(filename))
          os.remove(filename)

      # Remove directories of previous versions in the format:
      # {project name}-{version}
      filenames = glob.glob(u'{0:s}-*'.format(project_name))
      for filename in filenames:
        if not filenames_to_ignore.match(filename):
          if os.path.isdir(filename):
            logging.info(u'Removing: {0:s}'.format(filename))
            shutil.rmtree(filename)

      if self._build_target == 'download':
        # If available run the script post-download.sh after download.
        if os.path.exists(u'post-download.sh'):
          command = u'sh ./post-download.sh {0:s}'.format(source_filename)
          exit_code = subprocess.call(command, shell=True)
          if exit_code != 0:
            logging.error(u'Running: "{0:s}" failed.'.format(command))
            return False

      elif self._build_target == 'msi':
        logging.info(u'Not implemented yet.')
        return False

      elif project_name in self._LIBYAL_LIBRARIES:
        if not self._BuildLibyalLibrary(
            source_filename, project_name, project_version):
          return False

      elif project_name in self._PYTHON_MODULES:
        if not self._BuildPythonModule(
            download_helper, source_filename, project_name, project_version,
            project_information):
          return False

    return True

  def _BuildLibyalLibrary(
      self, source_filename, project_name, project_version):
    """Builds a libyal library and its Python module dependency.

    Args:
      source_filename: the name of the source package file.
      project_name: the name of the project
      project_version: the version of the project.

    Returns:
      True if the build is successful or False on error.
    """
    build_helper = None
    if self._build_target == 'dpkg':
      build_helper = LibyalDpkgBuildHelper()
      deb_filename = build_helper.GetOutputFilename(
          project_name, project_version)

      build_helper.Clean(project_name, project_version)

      if not os.path.exists(deb_filename):
        logging.info(u'Building deb of: {0:s}'.format(source_filename))
        if not build_helper.Build(source_filename):
          logging.info(
              u'Build of: {0:s} failed for more info check {1:s}'.format(
                  source_filename, os.path.abspath(build_helper.LOG_FILENAME)))
          return False

    elif self._build_target == 'pkg':
      build_helper = LibyalPkgBuildHelper()
      dmg_filename = build_helper.GetOutputFilename(
          project_name, project_version)

      build_helper.Clean(project_name, project_version)

      if not os.path.exists(dmg_filename):
        logging.info(u'Building pkg of: {0:s}'.format(source_filename))
        if not build_helper.Build(
            source_filename, project_name, project_version):
          logging.info(
              u'Build of: {0:s} failed for more info check {1:s}'.format(
                  source_filename, os.path.abspath(build_helper.LOG_FILENAME)))
          return False

    elif self._build_target == 'rpm':
      build_helper = LibyalRpmBuildHelper()
      rpm_filename = build_helper.GetOutputFilename(
          project_name, project_version)

      build_helper.Clean(project_name, project_version)

      if not os.path.exists(rpm_filename):
        # TODO: move the rename into the builder class?

        # rpmbuild wants the library filename without the status indication.
        rpm_source_filename = u'{0:s}-{1!s}.tar.gz'.format(
            project_name, project_version)
        os.rename(source_filename, rpm_source_filename)

        logging.info(u'Building rpm of: {0:s}'.format(source_filename))
        build_successful = build_helper.Build(
            rpm_source_filename, project_name, project_version)

        # Change the library filename back to the original.
        os.rename(rpm_source_filename, source_filename)

        if not build_successful:
          logging.info(
              u'Build of: {0:s} failed for more info check {1:s}'.format(
                  source_filename, os.path.abspath(build_helper.LOG_FILENAME)))
          return False

    if build_helper and os.path.exists(build_helper.LOG_FILENAME):
      logging.info(u'Removing: {0:s}'.format(build_helper.LOG_FILENAME))
      os.remove(build_helper.LOG_FILENAME)

    return True

  def _BuildPythonModule(
      self, download_helper, source_filename, project_name, project_version,
      project_information):
    """Builds a Python module dependency.

    Args:
      download_helper: the download helper (instance of DownloadHelper).
      source_filename: the name of the source package file.
      project_name: the name of the project
      project_version: the version of the project.
      project_information: a dictionary object containing project information
                           values.

    Returns:
      True if the build is successful or False on error.
    """
    build_helper = None
    if self._build_target == 'dpkg':
      build_helper = PythonModuleDpkgBuildHelper()
      deb_filename = build_helper.GetOutputFilename(
          project_name, project_version)

      build_helper.Clean(project_name, project_version)

      if not os.path.exists(deb_filename):
        logging.info(u'Building deb of: {0:s}'.format(source_filename))
        if not build_helper.Build(
            source_filename, project_name, project_version,
            project_information, self._plaso_path):
          logging.info(
              u'Build of: {0:s} failed for more info check {1:s}'.format(
                  source_filename, os.path.abspath(build_helper.LOG_FILENAME)))
          return False

    elif self._build_target == 'pkg':
      build_helper = PythonModulePkgBuildHelper()
      pkg_filename = build_helper.GetOutputFilename(
          project_name, project_version)

      build_helper.Clean(project_name, project_version)

      if not os.path.exists(pkg_filename):
        project_identifier = download_helper.GetProjectIdentifier(
            project_name)

        logging.info(u'Building pkg of: {0:s}'.format(source_filename))
        build_successful = build_helper.Build(
            source_filename, project_name, project_version,
            project_identifier)

        if not build_successful:
          logging.info(
              u'Build of: {0:s} failed for more info check {1:s}'.format(
                  source_filename, os.path.abspath(build_helper.LOG_FILENAME)))
          return False

    elif self._build_target == 'rpm':
      build_helper = PythonModuleRpmBuildHelper()
      rpm_filename = build_helper.GetOutputFilename(
          project_name, project_version)

      build_helper.Clean(project_name, project_version)

      if not os.path.exists(rpm_filename):
        logging.info(u'Building rpm of: {0:s}'.format(source_filename))
        build_successful = build_helper.Build(
            source_filename, project_name, project_version)

        if not build_successful:
          logging.info(
              u'Build of: {0:s} failed for more info check {1:s}'.format(
                  source_filename, os.path.abspath(build_helper.LOG_FILENAME)))
          return False

    if build_helper and os.path.exists(build_helper.LOG_FILENAME):
      logging.info(u'Removing: {0:s}'.format(build_helper.LOG_FILENAME))
      os.remove(build_helper.LOG_FILENAME)

    return True

  def Build(self, project_name, project_type, project_information):
    """Builds a dependency.

    Args:
      project_name: the project name.
      project_type: the project type.
      project_information: a dictionary object containing project information
                           values.

    Returns:
      True if the build is successful or False on error.

    Raises:
      ValueError: if the project type is unsupported.
    """
    if project_type == self.PROJECT_TYPE_GOOGLE_CODE_WIKI:
      download_helper = GoogleCodeWikiDownloadHelper()
    elif project_type == self.PROJECT_TYPE_PYPI:
      download_helper = PyPiDownloadHelper()
    elif project_type == self.PROJECT_TYPE_SOURCE_FORGE:
      download_helper = SourceForgeDownloadHelper()
    elif project_type == self.PROJECT_TYPE_GITHUB_LIBYAL:
      download_helper = LibyalGitHubDownloadHelper()
    elif project_type == self.PROJECT_TYPE_GITHUB_LOG2TIMELINE:
      download_helper = Log2TimelineGitHubDownloadHelper()
    else:
      raise ValueError(u'Unsupported project type.')

    return self._BuildDependency(
        download_helper, project_name, project_information)


def Main():
  build_targets = frozenset(['download', 'dpkg', 'msi', 'pkg', 'rpm'])

  args_parser = argparse.ArgumentParser(description=(
      'Downloads and builds the latest versions of plaso dependencies.'))

  args_parser.add_argument(
      '--build-directory', '--build_directory', action='store',
      metavar='DIRECTORY', dest='build_directory', type=unicode,
      default=u'dependencies', help=(
          u'The location of the the build directory.'))

  args_parser.add_argument(
      'build_target', choices=sorted(build_targets), action='store',
      metavar='BUILD_TARGET', default=None, help='The build target.')

  options = args_parser.parse_args()

  if not options.build_target:
    print u'Build target missing.'
    print u''
    args_parser.print_help()
    print u''
    return False

  if options.build_target not in build_targets:
    print u'Unsupported build target: {0:s}.'.format(options.build_target)
    print u''
    args_parser.print_help()
    print u''
    return False

  logging.basicConfig(
      level=logging.INFO, format=u'[%(levelname)s] %(message)s')

  if options.build_target == 'dpkg':
    missing_packages = DpkgBuildHelper.CheckBuildDependencies()
    if missing_packages:
      print (u'Required build package(s) missing. Please install: '
             u'{0:s}.'.format(u', '.join(missing_packages)))
      print u''
      return False

  elif options.build_target == 'rpm':
    missing_packages = RpmBuildHelper.CheckBuildDependencies()
    if missing_packages:
      print (u'Required build package(s) missing. Please install: '
             u'{0:s}.'.format(u', '.join(missing_packages)))
      print u''
      return False

  # __file__ will point to a different location when access later in
  # the script. So we need to preserve the location of the plaso source
  # files here for future usage.
  plaso_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
  dependency_builder = DependencyBuilder(options.build_target, plaso_path)

  # TODO: allow for patching e.g. dpkt 1.8.
  # Have builder check patches URL.

  # TODO: package ipython.

  # TODO:
  # (u'protobuf', DependencyBuilder.PROJECT_TYPE_GOOGLE_CODE_WIKI),
  # ./configure
  # make
  # cd python
  # python setup.py build
  # python setup.py install --root $PWD/tmp
  #
  # Build of rpm fails:
  # python setup.py bdist_rpm
  #
  # Solution: use protobuf-python.spec to build

  # TODO: download and build sqlite3 from source?

  # TODO: rpm build of psutil is broken, fix upstream or add patching.
  # (u'psutil', DependencyBuilder.PROJECT_TYPE_PYPI),

  # TODO: generate dpkg files instead of downloading them or
  # download and override version information.

  # TODO: python-tz add tzdata dependency.

  builds = [
    (u'bencode', DependencyBuilder.PROJECT_TYPE_PYPI, {
        'upstream_maintainer': u'Thomas Rampelberg <thomas@bittorrent.com>',
        'upstream_homepage': u'http://bittorent.com/',
        'description_short': (
            u'The BitTorrent bencode module as light-weight, standalone '
            u'package'),
        'description_long': (
            u'The BitTorrent bencode module as light-weight, standalone '
            u'package.')}),

    (u'binplist', DependencyBuilder.PROJECT_TYPE_GOOGLE_CODE_WIKI, {}),
    (u'construct', DependencyBuilder.PROJECT_TYPE_PYPI, {
        'upstream_maintainer': u'Tomer Filiba <tomerfiliba@gmail.com>',
        'upstream_homepage': u'http://construct.readthedocs.org/en/latest/',
        'description_short': (
            u'Construct is a powerful declarative parser (and builder) for '
            u'binary data'),
        'description_long': (
            u'Construct is a powerful declarative parser (and builder) for '
            u'binary data.')}),

    (u'dfvfs', DependencyBuilder.PROJECT_TYPE_GITHUB_LOG2TIMELINE, {}),
    (u'dpkt', DependencyBuilder.PROJECT_TYPE_GOOGLE_CODE_WIKI, {
        'upstream_maintainer': u'Dug Song <dugsong@monkey.org>',
        'upstream_homepage': u'https://code.google.com/p/dpkt/',
        'description_short': (
            u'Python packet creation / parsing module'),
        'description_long': (
            u'Python module for fast, simple packet creation / parsing, '
            u'with definitions for the basic TCP/IP protocols.')}),

    (u'libbde', DependencyBuilder.PROJECT_TYPE_GITHUB_LIBYAL, {}),
    (u'libesedb', DependencyBuilder.PROJECT_TYPE_GITHUB_LIBYAL, {}),
    (u'libevt', DependencyBuilder.PROJECT_TYPE_GITHUB_LIBYAL, {}),
    (u'libevtx', DependencyBuilder.PROJECT_TYPE_GITHUB_LIBYAL, {}),
    (u'libewf', DependencyBuilder.PROJECT_TYPE_GITHUB_LIBYAL, {}),
    (u'libfwsi', DependencyBuilder.PROJECT_TYPE_GITHUB_LIBYAL, {}),
    (u'liblnk', DependencyBuilder.PROJECT_TYPE_GITHUB_LIBYAL, {}),
    (u'libmsiecf', DependencyBuilder.PROJECT_TYPE_GITHUB_LIBYAL, {}),
    (u'libolecf', DependencyBuilder.PROJECT_TYPE_GITHUB_LIBYAL, {}),
    (u'libqcow', DependencyBuilder.PROJECT_TYPE_GITHUB_LIBYAL, {}),
    (u'libregf', DependencyBuilder.PROJECT_TYPE_GITHUB_LIBYAL, {}),
    (u'libsmdev', DependencyBuilder.PROJECT_TYPE_GITHUB_LIBYAL, {}),
    (u'libsmraw', DependencyBuilder.PROJECT_TYPE_GITHUB_LIBYAL, {}),
    (u'libvhdi', DependencyBuilder.PROJECT_TYPE_GITHUB_LIBYAL, {}),
    (u'libvmdk', DependencyBuilder.PROJECT_TYPE_GITHUB_LIBYAL, {}),
    (u'libvshadow', DependencyBuilder.PROJECT_TYPE_GITHUB_LIBYAL, {}),
    (u'pyparsing', DependencyBuilder.PROJECT_TYPE_SOURCE_FORGE, {
        'upstream_maintainer': u'Paul McGuire <ptmcg@users.sourceforge.net>',
        'upstream_homepage': u'http://pyparsing.wikispaces.com/',
        'description_short': u'Python parsing module',
        'description_long': (
            u'The parsing module is an alternative approach to creating and '
            u'executing simple grammars, vs. the traditional lex/yacc '
            u'approach, or the use of regular expressions. The parsing '
            u'module provides a library of classes that client code uses '
            u'to construct the grammar directly in Python code.')}),

    (u'pysqlite', DependencyBuilder.PROJECT_TYPE_PYPI, {
        'upstream_maintainer': u'Gerhard Häring <gh@ghaering.de>',
        'upstream_homepage': u'https://pypi.python.org/pypi/pysqlite/',
        'description_short': u'Python interface to SQLite 3',
        'description_long': (
            u'pysqlite is a DB-API 2.0-compliant database interface for '
            u'SQLite.')}),

    (u'pytz', DependencyBuilder.PROJECT_TYPE_PYPI, {
        'upstream_maintainer': u'Stuart Bishop <stuart@stuartbishop.net>',
        'upstream_homepage': u'http://pypi.python.org/pypi/pytz/',
        'description_short': u'Python version of the Olson timezone database',
        'description_long': (
            u'python-tz brings the Olson tz database into Python. This library '
            u'allows accurate and cross platform timezone calculations using '
            u'Python 2.3 or higher. It also solves the issue of ambiguous '
            u'times at the end of daylight savings, which you can read more '
            u'about in the Python Library Reference (datetime.tzinfo).')}),

    (u'PyYAML', DependencyBuilder.PROJECT_TYPE_PYPI, {
        'upstream_maintainer': u'Kirill Simonov <xi@resolvent.net>',
        'upstream_homepage': u'http://pyyaml.org/',
        'description_short': u'YAML parser and emitter for Python',
        'description_long': (
            u'Python-yaml is a complete YAML 1.1 parser and emitter for '
            u'Python. It can parse all examples from the specification. '
            u'The parsing algorithm is simple enough to be a reference '
            u'for YAML parser implementors. A simple extension API is '
            u'also provided. The package is built using libyaml for '
            u'improved speed.')}),

    (u'six', DependencyBuilder.PROJECT_TYPE_PYPI, {
        'upstream_maintainer': u'Benjamin Peterson <benjamin@python.org>',
        'upstream_homepage': u'http://pypi.python.org/pypi/six/',
        'description_short': (
            u'Python 2 and 3 compatibility library (Python 2 interface)'),
        'description_long': (
            u'Six is a Python 2 and 3 compatibility library. It provides '
            u'utility functions for smoothing over the differences between '
            u'the Python versions with the goal of writing Python code that '
            u'is compatible on both Python versions.')})]

  if not os.path.exists(options.build_directory):
    os.mkdir(options.build_directory)

  current_working_directory = os.getcwd()
  os.chdir(options.build_directory)

  result = True
  for project_name, project_type, project_information in builds:
    if not dependency_builder.Build(
        project_name, project_type, project_information):
      print u'Failed building: {0:s}'.format(project_name)
      result = False
      break

  os.chdir(current_working_directory)

  return result


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
