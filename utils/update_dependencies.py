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
"""Script to update prebuilt versions of the dependencies."""

import argparse
import glob
import logging
import os
import platform
import re
import subprocess
import sys
import urllib2

if platform.system() == 'Windows':
  import wmi


class DownloadHelper(object):
  """Class that helps in downloading a project."""

  def __init__(self):
    """Initializes the build helper."""
    super(DownloadHelper, self).__init__()
    self._cached_url = u''
    self._cached_page_content = ''

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


class GoogleCodeDownloadHelper(DownloadHelper):
  """Class that helps in downloading a Google Code project."""

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

  def GetPackageDownloadUrls(self, google_drive_url):
    """Retrieves the package downloads URL for a given URL.

    Args:
      google_drive_url: the Google Drive URL.

    Returns:
      A list of package download URLs.
    """
    page_content = self.DownloadPageContent(google_drive_url)
    if not page_content:
      return

    # The format of the project download URL is:
    # /host/{random string}/3rd%20party/{sub directory}/{filename}
    expression_string = u'/host/[^/]+/3rd%20party/[^/">]+/[^">]+'
    matches = re.findall(expression_string, page_content)

    for match_index in range(0, len(matches)):
      matches[match_index] = u'https://googledrive.com{0:s}'.format(
          matches[match_index])

    return matches

  def Download(self, download_url):
    """Downloads the project for a given project name and version.

    Args:
      download_url: the download URL.

    Returns:
      The filename if successful also if the file was already downloaded
      or None on error.
    """
    return self.DownloadFile(download_url)


def CompareVersions(first_version_list, second_version_list):
  """Compares two lists containing version parts.

  Note that the version parts can contain alpha numeric characters.

  Args:
    first_version_list: the first list of version parts.
    second_version_list: the second list of version parts.

  Returns:
    1 if the first is larger than the second, -1 if the first is smaller than
    the second, or 0 if the first and second are equal.
  """
  first_version_list_length = len(first_version_list)
  second_version_list_length = len(second_version_list)

  for index in range(0, first_version_list_length):
    if index >= second_version_list_length:
      return 1

    if first_version_list[index] > second_version_list[index]:
      return 1
    elif first_version_list[index] < second_version_list[index]:
      return -1

  if first_version_list_length < second_version_list_length:
    return -1

  return 0


def Main():
  args_parser = argparse.ArgumentParser(description=(
      u'Installs the latest versions of plaso dependencies.'))

  args_parser.add_argument(
      '-f', '--force', dest='force_install', action='store_true',
      default=False, help=(
          u'Force installation. This option removes existing versions '
          u'of installed dependencies. The default behavior is to only'
          u'install a dependency if not or an older version is installed.'))

  options = args_parser.parse_args()

  operating_system = platform.system()
  cpu_architecture = platform.machine().lower()
  linux_name = None
  sub_directory = None
  noarch_sub_directory = None

  if operating_system == u'Darwin':
    # TODO: determine OSX version
    if cpu_architecture != u'x86_64':
      logging.error(u'CPU architecture: {0:s} not supported.'.format(
          cpu_architecture))

    # Note that the sub directory should be URL encoded.
    sub_directory = u'macosx%2010.10'

  elif operating_system == u'Linux':
    linux_name, linux_version, _ = platform.linux_distribution()
    if linux_name == u'Fedora' and linux_version == u'20':
      if cpu_architecture != u'x86_64':
        logging.error(u'CPU architecture: {0:s} not supported.'.format(
            cpu_architecture))

      sub_directory = u'fedora20-x86_64'
      noarch_sub_directory = u'fedora20-noarch'

    elif linux_name == u'Ubuntu' and linux_version == u'12.04':
      if cpu_architecture == u'i686':
        sub_directory = u'ubuntu12.04-i386'
        noarch_sub_directory = u'ubuntu12.04-all'

      elif cpu_architecture == u'x86_64':
        sub_directory = u'ubuntu12.04-amd64'
        noarch_sub_directory = u'ubuntu12.04-all'

      else:
        logging.error(u'CPU architecture: {0:s} not supported.'.format(
            cpu_architecture))

    else:
      logging.error(u'Linux variant: {0:s} {1:s} not supported.'.format(
          linux_name, linux_version))

  elif operating_system == u'Windows':
    if cpu_architecture == u'x86':
      sub_directory = u'win32-vs2008'

    elif cpu_architecture == u'amd64':
      sub_directory = u'win-amd64-vs2010'

    else:
      logging.error(u'CPU architecture: {0:s} not supported.'.format(
          cpu_architecture))

  else:
    logging.error(u'Operating system: {0:s} not supported.'.format(
        operating_system))
    return False

  download_helper = GoogleCodeDownloadHelper()
  google_drive_url = download_helper.GetGoogleCodeDownloadsUrl(u'plaso')

  package_urls = download_helper.GetPackageDownloadUrls(
      u'{0:s}/3rd%20party/{1:s}'.format(google_drive_url, sub_directory))

  if noarch_sub_directory:
    noarch_package_urls = download_helper.GetPackageDownloadUrls(
        u'{0:s}/3rd%20party/{1:s}'.format(
            google_drive_url, noarch_sub_directory))

    package_urls.extend(noarch_package_urls)

  dependencies_directory = u'dependencies'
  if not os.path.exists(dependencies_directory):
    os.mkdir(dependencies_directory)

  os.chdir(dependencies_directory)

  package_filenames = {}
  package_versions = {}
  for package_url in package_urls:
    _, _, package_filename = package_url.rpartition(u'/')
    if package_filename.endswith(u'.deb'):
      name, _, version = package_filename.partition(u'_')

      # Ignore devel and tools DEB packages.
      if name.endswith(u'-dev') or name.endswith(u'-tools'):
        continue

      if name.endswith(u'-python'):
        package_prefix = name
        name, _, _ = name.partition(u'-')
      else:
        package_prefix = u'{0:s}_'.format(name)
      version, _, _ = version.partition(u'-')

    elif package_filename.endswith(u'.dmg'):
      name, _, version = package_filename.partition(u'-')
      version, _, _ = version.partition(u'.dmg')
      package_prefix = name

    elif package_filename.endswith(u'.msi'):
      name, _, version = package_filename.partition(u'-')
      version, _, _ = version.partition(u'.win')
      package_prefix = name

    elif package_filename.endswith(u'.rpm'):
      name, _, version = package_filename.partition(u'-')

      # Ignore debuginfo, devel and tools RPM packages.
      if (version.startswith(u'debuginfo') or version.startswith(u'devel') or
          version.startswith(u'tools')):
        continue

      # Ignore the sleuthkit tools RPM package.
      if name == u'sleuthkit' and not version.startswith(u'libs'):
        continue

      package_prefix, _, version = version.partition(u'-')
      version, _, _ = version.partition(u'-')
      package_prefix = u'{0:s}-{1:s}'.format(name, package_prefix)

    else:
      # Ignore all other file exensions.
      continue

    version = version.split(u'.')
    if name == u'pytsk':
      last_part = version.pop()
      version.extend(last_part.split(u'-'))

    if name not in package_versions:
      compare_result = 1
    else:
      compare_result = CompareVersions(version, package_versions[name])

    if compare_result > 0:
      package_filenames[name] = package_filename
      package_versions[name] = version

    if not os.path.exists(package_filename):
      filenames = glob.glob(u'{0:s}*'.format(package_prefix))
      for filename in filenames:
        print u'Removing: {0:s}'.format(filename)
        os.remove(filename)

      print u'Downloading: {0:s}'.format(package_filename)
      _ = download_helper.Download(package_url)

  os.chdir(u'..')

  if operating_system == u'Darwin':
    result = True

    command = u'/usr/sbin/pkgutil --packages'
    print 'Running: "{0:s}"'.format(command)
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    if process.returncode is None:
      packages, _ = process.communicate()
    else:
      packages = ''

    if process.returncode != 0:
      logging.error(u'Running: "{0:s}" failed.'.format(command))
      return False

    for package_name in packages.split('\n'):
      if not package_name:
        continue

      if (package_name.startswith(u'com.github.libyal.') or
          package_name.startswith(u'com.github.log2timeline.') or
          package_name.startswith(u'com.github.sleuthkit.') or
          package_name.startswith(u'com.google.code.p.') or
          package_name.startswith(u'org.samba.') or
          package_name.startswith(u'org.python.pypi.') or
          package_name.startswith(u'net.sourceforge.projects.')):

        if package_name.startswith(u'com.github.libyal.'):
          name = package_name[18:]

        elif package_name.startswith(u'com.github.log2timeline.'):
          name = package_name[24:]

        elif package_name.startswith(u'com.github.sleuthkit.'):
          name = package_name[21:]

        elif package_name.startswith(u'com.google.code.p.'):
          name = package_name[18:]

        elif package_name.startswith(u'org.samba.'):
          name = package_name[10:]

        elif package_name.startswith(u'org.python.pypi.'):
          name = package_name[16:]

        elif package_name.startswith(u'net.sourceforge.projects.'):
          name = package_name[25:]

        # Detect the PackageMaker naming convention.
        if name.endswith(u'.pkg'):
          _, _, sub_name = name[:-4].rpartition(u'.')
          is_package_maker_pkg = True
        else:
          is_package_maker_pkg = False
        name, _, _ = name.partition(u'.')

        if name in package_versions:
          # Determine the package version.
          command = u'/usr/sbin/pkgutil --pkg-info {0:s}'.format(package_name)
          print 'Running: "{0:s}"'.format(command)
          process = subprocess.Popen(
              command, stdout=subprocess.PIPE, shell=True)
          if process.returncode is None:
            package_info, _ = process.communicate()
          else:
            package_info = ''

          if process.returncode != 0:
            logging.error(u'Running: "{0:s}" failed.'.format(command))
            result = False
            continue

          location = None
          version = None
          volume = None
          for attribute in package_info.split('\n'):
            if attribute.startswith(u'location: '):
              _, _, location = attribute.rpartition(u'location: ')

            elif attribute.startswith(u'version: '):
              _, _, version = attribute.rpartition(u'version: ')

            elif attribute.startswith(u'volume: '):
              _, _, volume = attribute.rpartition(u'volume: ')

          version = version.split(u'.')
          if options.force_install:
            compare_result = -1
          elif name not in package_versions:
            compare_result = 1
          # TODO: handle pytsk.
          else:
            compare_result = CompareVersions(version, package_versions[name])
            if compare_result >= 0:
              # The latest or newer version is already installed.
              del package_versions[name]

          if compare_result < 0:
            # Determine the files in the package.
            command = u'/usr/sbin/pkgutil --files {0:s}'.format(package_name)
            print 'Running: "{0:s}"'.format(command)
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, shell=True)
            if process.returncode is None:
              package_files, _ = process.communicate()
            else:
              package_files = ''

            if process.returncode != 0:
              logging.error(u'Running: "{0:s}" failed.'.format(command))
              result = False
              continue

            directories = []
            files = []
            for filename in package_files.split('\n'):
              if is_package_maker_pkg:
                filename = u'{0:s}{1:s}/{2:s}/{3:s}'.format(
                    volume, location, sub_name, filename)
              else:
                filename = u'{0:s}{1:s}'.format(location, filename)

              if os.path.isdir(filename):
                directories.append(filename)
              else:
                files.append(filename)

            print 'Removing: {0:s} {1:s}'.format(name, version)
            for filename in files:
              if os.path.exists(filename):
                os.remove(filename)

            for filename in directories:
              if os.path.exists(filename):
                try:
                  os.rmdir(filename)
                except OSError:
                  # Ignore directories that are not empty.
                  pass

            command = u'/usr/sbin/pkgutil --forget {0:s}'.format(
                package_name)
            exit_code = subprocess.call(command, shell=True)
            if exit_code != 0:
              logging.error(u'Running: "{0:s}" failed.'.format(command))
              result = False

    if not result:
      return False

  elif operating_system == u'Windows':
    connection = wmi.WMI()

    query = u'SELECT Name FROM Win32_Product'
    for product in connection.query(query):
      name = getattr(product, 'Name', u'')
      # Windows package names start with 'Python' or 'Python 2.7 '.
      if name.startswith('Python '):
        _, _, name = name.rpartition(u' ')
        if name.startswith('2.7 '):
          _, _, name = name.rpartition(u' ')

        name, _, version = name.partition(u'-')

        version = version.split(u'.')
        if options.force_install:
          compare_result = -1
        elif name not in package_versions:
          compare_result = 1
        elif name == u'pytsk':
          # We cannot really tell by the version number that pytsk needs to
          # be update. Just update it any way.
          compare_result = -1
        else:
          compare_result = CompareVersions(version, package_versions[name])
          if compare_result >= 0:
            # The latest or newer version is already installed.
            del package_versions[name]

        if compare_result < 0:
          print 'Removing: {0:s} {1:s}'.format(name, u'.'.join(version))
          product.Uninstall()

  result = True

  if operating_system == u'Darwin':
    for name, version in package_versions.iteritems():
      package_filename = package_filenames[name]

      command = u'sudo /usr/bin/hdiutil attach {0:s}'.format(
          os.path.join(dependencies_directory, package_filename))
      print 'Running: "{0:s}"'.format(command)
      exit_code = subprocess.call(command, shell=True)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        result = False
        continue

      volume_path = u'/Volumes/{0:s}.pkg'.format(package_filename[:-4])
      if not os.path.exists(volume_path):
        logging.error(u'Missing volume: {0:s}.'.format(volume_path))
        result = False
        continue

      pkg_file = u'{0:s}/{1:s}.pkg'.format(volume_path, package_filename[:-4])
      if not os.path.exists(pkg_file):
        logging.error(u'Missing pkg file: {0:s}.'.format(pkg_file))
        result = False
        continue

      command = u'sudo /usr/sbin/installer -target / -pkg {0:s}'.format(
          pkg_file)
      print 'Running: "{0:s}"'.format(command)
      exit_code = subprocess.call(command, shell=True)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        result = False

      command = u'sudo /usr/bin/hdiutil detach {0:s}'.format(volume_path)
      print 'Running: "{0:s}"'.format(command)
      exit_code = subprocess.call(command, shell=True)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        result = False

  elif operating_system == u'Linux':
    if linux_name == u'Fedora':
      # TODO: move these to a separate file?
      dependencies = [
          u'ipython',
          u'libyaml'
          u'python-dateutil',
          u'pyparsing',
          u'pytz',
          u'PyYAML',
          u'protobuf-python']

      command = u'sudo yum install {0:s}'.format(u' '.join(dependencies))
      print 'Running: "{0:s}"'.format(command)
      exit_code = subprocess.call(command, shell=True)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        result = False

      command = u'sudo rpm -Fvh {0:s}/*'.format(dependencies_directory)
      print 'Running: "{0:s}"'.format(command)
      exit_code = subprocess.call(command, shell=True)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        result = False

    elif linux_name == u'Ubuntu':
      # TODO: add -dbg package support.
      # TODO: move these to a separate file?
      dependencies = [
          u'ipython',
          u'libprotobuf7',
          u'libyaml-0-2',
          u'python-bencode',
          u'python-dateutil',
          u'python-dpkt',
          u'python-hachoir-core',
          u'python-hachoir-metadata',
          u'python-hachoir-parser',
          u'python-protobuf',
          u'python-six',
          u'python-tz',
          u'python-yaml']

      command = u'sudo apt-get install {0:s}'.format(u' '.join(dependencies))
      print 'Running: "{0:s}"'.format(command)
      exit_code = subprocess.call(command, shell=True)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        result = False

      command = u'sudo dpkg -i {0:s}/*.deb'.format(dependencies_directory)
      print 'Running: "{0:s}"'.format(command)
      exit_code = subprocess.call(command, shell=True)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        result = False

  elif operating_system == u'Windows':
    for name, version in package_versions.iteritems():
      # TODO: add RunAs ?
      package_filename = package_filenames[name]
      command = u'msiexec.exe /i {0:s} /q'.format(os.path.join(
          dependencies_directory, package_filename))
      print 'Installing: {0:s} {1:s}'.format(name, u'.'.join(version))
      exit_code = subprocess.call(command, shell=False)
      if exit_code != 0:
        logging.error(u'Running: "{0:s}" failed.'.format(command))
        result = False

  return result


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
