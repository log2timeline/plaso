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
import logging
import os
import re
import shutil
import subprocess
import sys
import tarfile
import urllib2


# TODO: look into merging functionality with update dependencies script.


class DownloadHelper(object):
  """Class that helps in downloading a project."""

  def __init__(self):
    """Initializes the build helper."""
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


class BuildFilesDownloadHelper(DownloadHelper):
  """Class that helps in downloading build files."""

  _BASE_URL = (
    u'https://googledrive.com/host/0B30H7z4S52FleW5vUHBnblJfcjg/'
    u'3rd%20party/build-files')

  def GetDownloadUrl(self, project_name, project_version):
    """Retrieves the download URL for a given project name and version.

    Args:
      project_name: the name of the project.
      project_version: the version of the project.

    Returns:
      The download URL of the project or None on error.
    """
    filename = u'{0:s}-{1:s}-dpkg.tar.gz'.format(
        project_name, project_version)
    return u'/'.join([self._BASE_URL, filename])


class GoogleCodeDownloadHelper(DownloadHelper):
  """Class that helps in downloading a Google code project."""

  def GetGoogleCodeDownloadsUrl(self, project_name):
    """Retrieves the Download URL from the Google Code project page.

    Args:
      project_name: the name of the project.

    Returns:
      The downloads URL or None on error.
    """
    download_url = u'https://code.google.com/p/{0:s}/'.format(project_name)

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return

    # The format of the project downloads URL is:
    # https://googledrive.com/host/{random string}/
    expression_string = (
        u'<a href="(https://googledrive.com/host/[^/]*/)"[^>]*>Downloads</a>')
    matches = re.findall(expression_string, page_content)

    if not matches or len(matches) != 1:
      return

    return matches[0]

  def GetLatestVersion(self, project_name):
    """Retrieves the latest version number for a given project name.

    Args:
      project_name: the name of the project.

    Returns:
      The a string containing the latest version number or None on error.
    """
    download_url = self.GetGoogleCodeDownloadsUrl(project_name)

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return

    # The format of the project download URL is:
    # /host/{random string}/{project name}-{status-}{version}.tar.gz
    # Note that the status is optional and will be: beta, alpha or experimental.
    expression_string = u'/host/[^/]*/{0:s}-[a-z-]*([0-9]+)[.]tar[.]gz'.format(
        project_name)
    matches = re.findall(expression_string, page_content)

    if not matches:
      return

    return unicode(max(matches))

  def GetDownloadUrl(self, project_name, project_version):
    """Retrieves the download URL for a given project name and version.

    Args:
      project_name: the name of the project.
      project_version: the version of the project.

    Returns:
      The download URL of the project or None on error.
    """
    download_url = self.GetGoogleCodeDownloadsUrl(project_name)

    page_content = self.DownloadPageContent(download_url)
    if not page_content:
      return

    # The format of the project download URL is:
    # /host/{random string}/{project name}-{status-}{version}.tar.gz
    # Note that the status is optional and will be: beta, alpha or experimental.
    expression_string = u'/host/[^/]*/{0:s}-[a-z-]*{1:s}[.]tar[.]gz'.format(
        project_name, project_version)
    matches = re.findall(expression_string, page_content)

    if not matches or len(matches) != 1:
      return

    return u'https://googledrive.com{0:s}'.format(matches[0])


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


class BuildHelper(object):
  """Base class that helps in building."""

  LOG_FILENAME = u'build.log'

  def __init__(self):
    """Initializes the build helper."""
    super(BuildHelper, self).__init__()

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

    archive = tarfile.open(source_filename, 'r:gz', encoding='utf-8')
    directory_name = ''

    for tar_info in archive.getmembers():
      filename = getattr(tar_info, 'name', None)
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

  def __init__(self):
    """Initializes the build helper."""
    super(DpkgBuildHelper, self).__init__()

  def _BuildPrepare(self, source_directory):
    """Make the necassary preperations before building the dpkg packages.

    Args:
      source_directory: the name of the source directory.

    Returns:
      True if the preparations were successful, False otherwise.
    """
    # Script to run before building, e.g. to change the dpkg packing files.
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
    # Script to run after building, e.g. to automatically upload the dpkg
    # package files to an apt repository.
    if os.path.exists(u'post-dpkg.sh'):
      command = u'sh ../post-dpkg.sh'
      exit_code = subprocess.call(
          u'(cd {0:s} && {1:s})'.format(source_directory, command), shell=True)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        return False

    return True

  def Build(self, source_filename, project_name, project_version):
    """Builds the dpkg packages.

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

    dpkg_directory = os.path.join(source_directory, u'dpkg')
    if not os.path.exists(dpkg_directory):
      dpkg_directory = os.path.join(source_directory, u'config', u'dpkg')

    if not os.path.exists(dpkg_directory):
      # Download the dpkg build files if necessary.
      os.chdir(source_directory)

      build_files_download_helper = BuildFilesDownloadHelper()
      build_files = build_files_download_helper.Download(
          project_name, project_version)

      build_files_build_helper = BuildHelper()
      dpkg_directory = build_files_build_helper.Extract(build_files)
      dpkg_directory = os.path.join(source_directory, dpkg_directory)

      os.chdir(u'..')

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

    command = u'dpkg-buildpackage -rfakeroot > {0:s} 2>&1'.format(
        os.path.join(u'..', self.LOG_FILENAME))
    exit_code = subprocess.call(
        u'(cd {0:s} && {1:s})'.format(source_directory, command), shell=True)
    if exit_code != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    if not self._BuildFinalize(source_directory):
      return False

    return True


class PythonModuleDpkgBuildHelper(DpkgBuildHelper):
  """Class that helps in building python module dpkg packages (.deb)."""

  def __init__(self):
    """Initializes the build helper."""
    super(PythonModuleDpkgBuildHelper, self).__init__()

  def Clean(self, project_name, project_version):
    """Cleans the dpkg packages in the current directory.

    Args:
      project_name: the name of the project.
      project_version: the version of the project.
    """
    filenames_to_ignore = re.compile(
        u'^python-{0:s}[-_].*{1:s}'.format(project_name, project_version))

    # Remove files of previous versions in the format:
    # python-{project name}[-_]{project version}-1_architecture.*
    filenames = glob.glob(
        u'python-{0:s}[-_]*[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]-1_'
        u'all.*'.format(project_name))

    for filename in filenames:
      if not filenames_to_ignore.match(filename):
        logging.info(u'Removing: {0:s}'.format(filename))
        os.remove(filename)

    # Remove files of previous versions in the format:
    # python-{project name}[-_]*version-1.*
    filenames = glob.glob(
        u'python-{0:s}[-_]*[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]-1.*'.format(
            project_name))

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
    # TODO: handle the conversion of some of the project names e.g.
    # pytz => python-tz
    return u'python-{0:s}_{1:s}-1_all.deb'.format(project_name, project_version)


class MsiBuildHelper(BuildHelper):
  """Class that helps in building Microsoft Installer packages (.msi)."""
  # TODO: implement.


class PkgBuildHelper(BuildHelper):
  """Class that helps in building PackageMaker packages (.pkg)."""
  # TODO: implement.


class RpmBuildHelper(BuildHelper):
  """Class that helps in building rpm packages (.rpm)."""

  def __init__(self):
    """Initializes the build helper."""
    super(RpmBuildHelper, self).__init__()


class PythonModuleRpmBuildHelper(RpmBuildHelper):
  """Class that helps in building rpm packages (.rpm)."""
  # TODO: move common rpm build helper code into RpmBuildHelper.

  def __init__(self):
    """Initializes the build helper."""
    super(PythonModuleRpmBuildHelper, self).__init__()

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
        source_directory, u'dist', u'{0:s}-{1:s}-1.noarch.rpm'.format(
            project_name, project_version)))
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
    filenames_to_ignore = re.compile(
        u'{0:s}-.*{1:s}-1.noarch.rpm'.format(project_name, project_version))

    rpm_filenames_glob = u'{0:s}-*-1.noarch.rpm'.format(project_name)

    filenames = glob.glob(rpm_filenames_glob)
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
    return u'{0:s}-{1:s}-1.noarch.rpm'.format(project_name, project_version)


class DependencyBuilder(object):
  """Class that helps in building dependencies."""

  _PATCHES_URL = (
    u'https://googledrive.com/host/0B30H7z4S52FleW5vUHBnblJfcjg/'
    u'3rd%20party/patches')

  PROJECT_TYPE_GOOGLE_CODE = 1
  PROJECT_TYPE_GOOGLE_CODE_WIKI = 2
  PROJECT_TYPE_PYPI = 3
  PROJECT_TYPE_SOURCE_FORGE = 4

  def __init__(self, build_target):
    """Initializes the dependency builder.

    Args:
      build_target: the build target.
    """
    super(DependencyBuilder, self).__init__()
    self._build_target = build_target

  def _BuildPythonModule(self, download_helper, project_name):
    """Builds a Python module dependency.

    Args:
      download_helper: the download helper (instance of DownloadHelper).
      project_name: the name of the project

    Returns:
      True if the build is successful or False on error.
    """
    project_version = download_helper.GetLatestVersion(project_name)
    if not project_version:
      logging.error(
          u'Unable to determine latest version of: {0:s}'.format(project_name))
      return False

    project_filename = download_helper.Download(project_name, project_version)

    if project_filename:
      filenames_to_ignore = re.compile(u'^{0:s}-.*{1:s}'.format(
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
      filenames = glob.glob(
          u'{0:s}-[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]'.format(
              project_name))
      for filename in filenames:
        if not filenames_to_ignore.match(filename):
          logging.info(u'Removing: {0:s}'.format(filename))
          shutil.rmtree(filename)

      if self._build_target == 'dpkg':
        build_helper = PythonModuleDpkgBuildHelper()
        deb_filename = build_helper.GetOutputFilename(
            project_name, project_version)

        build_helper.Clean(project_name, project_version)

        if not os.path.exists(deb_filename):
          logging.info(u'Building deb of: {0:s}'.format(project_filename))
          if not build_helper.Build(
              project_filename, project_name, project_version):
            logging.info(
                u'Build of: {0:s} failed for more info check {1:s}'.format(
                    project_filename, build_helper.LOG_FILENAME))
            return False

      elif self._build_target == 'download':
        # If available run the script post-download.sh after download.
        if os.path.exists(u'post-download.sh'):
          command = u'sh ./post-download.sh {0:s}'.format(project_filename)
          exit_code = subprocess.call(command, shell=True)
          if exit_code != 0:
            logging.error(u'Running: "{0:s}" failed.'.format(command))
            return False

      elif self._build_target == 'msi':
        logging.info(u'Not implemented yet.')
        return False

      elif self._build_target == 'pkg':
        logging.info(u'Not implemented yet.')
        return False

      elif self._build_target == 'rpm':
        build_helper = PythonModuleRpmBuildHelper()
        rpm_filename = build_helper.GetOutputFilename(
            project_name, project_version)

        build_helper.Clean(project_name, project_version)

        if not os.path.exists(rpm_filename):
          logging.info(u'Building rpm of: {0:s}'.format(project_filename))
          build_successful = build_helper.Build(
              project_filename, project_name, project_version)

          if not build_successful:
            logging.info(
                u'Build of: {0:s} failed for more info check {1:s}'.format(
                    project_filename, build_helper.LOG_FILENAME))
            return False

      if os.path.exists(build_helper.LOG_FILENAME):
        logging.info(u'Removing: {0:s}'.format(build_helper.LOG_FILENAME))
        os.remove(build_helper.LOG_FILENAME)

    return True

  def Build(self, project_name, project_type):
    """Builds a dependency.

    Args:
      project_name: the project name.
      project_type: the project type.

    Returns:
      True if the build is successful or False on error.

    Raises:
      ValueError: if the project type is unsupported.
    """
    if project_type == self.PROJECT_TYPE_GOOGLE_CODE:
      download_helper = GoogleCodeDownloadHelper()
    elif project_type == self.PROJECT_TYPE_GOOGLE_CODE_WIKI:
      download_helper = GoogleCodeWikiDownloadHelper()
    elif project_type == self.PROJECT_TYPE_PYPI:
      download_helper = PyPiDownloadHelper()
    elif project_type == self.PROJECT_TYPE_SOURCE_FORGE:
      download_helper = SourceForgeDownloadHelper()
    else:
      raise ValueError(u'Unsupported project type.')

    return self._BuildPythonModule(download_helper, project_name)


def Main():
  build_targets = frozenset(['download', 'dpkg', 'msi', 'pkg', 'rpm'])

  args_parser = argparse.ArgumentParser(description=(
      'Downloads and builds the latest versions of dfvfs.'))

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

  dependency_builder = DependencyBuilder(options.build_target)

  # TODO: allow for patching e.g. dpkt 1.8.
  # Have builder check patches URL.

  # TODO: use patches to provide missing packaging files, e.g. dpkg.

  # TODO:
  # protobuf
  # ipython

  # TODO: rpm build of psutil is broken, fix upstream or add patching.
  # (u'psutil', DependencyBuilder.PROJECT_TYPE_PYPI),

  # TODO: dependency sqlite-devel (rpm) or libsqlite3-dev (deb)
  # or download and build sqlite3 from source?

  # TODO: integrate libyal-sync?

  builds = [
    (u'bencode', DependencyBuilder.PROJECT_TYPE_PYPI),
    (u'binplist', DependencyBuilder.PROJECT_TYPE_GOOGLE_CODE_WIKI),
    (u'construct', DependencyBuilder.PROJECT_TYPE_PYPI),
    (u'dfvfs', DependencyBuilder.PROJECT_TYPE_GOOGLE_CODE),
    (u'dpkt', DependencyBuilder.PROJECT_TYPE_GOOGLE_CODE_WIKI),
    (u'pyparsing', DependencyBuilder.PROJECT_TYPE_SOURCE_FORGE),
    (u'pysqlite', DependencyBuilder.PROJECT_TYPE_PYPI),
    (u'pytz', DependencyBuilder.PROJECT_TYPE_PYPI),
    (u'PyYAML', DependencyBuilder.PROJECT_TYPE_PYPI),
    (u'six', DependencyBuilder.PROJECT_TYPE_PYPI)]

  build_directory = u'dependencies'
  if not os.path.exists(build_directory):
    os.mkdir(build_directory)
  os.chdir(build_directory)

  result = True
  for project_name, project_type in builds:
    if not dependency_builder.Build(project_name, project_type):
      print u'Failed building: {0:s}'.format(project_name)
      result = False
      break

  os.chdir(u'..')

  return result


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
