# -*- coding: utf-8 -*-
"""Linux preprocessor plugins."""

import csv
import datetime

from dateutil import tz

from dfvfs.helpers import text_file as dfvfs_text_file

from plaso.containers import artifacts
from plaso.lib import errors
from plaso.lib import line_reader_file
from plaso.preprocessors import interface
from plaso.preprocessors import manager


class LinuxHostnamePlugin(interface.FileArtifactPreprocessorPlugin):
  """The Linux hostname plugin."""

  ARTIFACT_DEFINITION_NAME = 'LinuxHostnameFile'

  def _ParseFileData(self, mediator, file_object):
    """Parses file content (data) for a hostname preprocessing attribute.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.
      file_object (dfvfs.FileIO): file-like object that contains the artifact
          value data.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    text_file_object = dfvfs_text_file.TextFile(file_object, encoding='utf-8')

    hostname = text_file_object.readline()
    hostname = hostname.strip()
    if hostname:
      hostname_artifact = artifacts.HostnameArtifact(name=hostname)
      mediator.AddHostname(hostname_artifact)


class LinuxDistributionPlugin(interface.FileArtifactPreprocessorPlugin):
  """The Linux distribution plugin."""

  ARTIFACT_DEFINITION_NAME = 'LinuxDistributionRelease'

  def _ParseFileData(self, mediator, file_object):
    """Parses file content (data) for system product preprocessing attribute.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.
      file_object (dfvfs.FileIO): file-like object that contains the artifact
          value data.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    text_file_object = dfvfs_text_file.TextFile(file_object, encoding='utf-8')

    system_product = text_file_object.readline()
    system_product = system_product.strip()

    if system_product:
      mediator.SetValue('operating_system_product', system_product)


class LinuxIssueFilePlugin(interface.FileArtifactPreprocessorPlugin):
  """The Linux issue file plugin."""

  ARTIFACT_DEFINITION_NAME = 'LinuxIssueFile'

  def _ParseFileData(self, mediator, file_object):
    """Parses file content (data) for system product preprocessing attribute.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.
      file_object (dfvfs.FileIO): file-like object that contains the artifact
          value data.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    text_file_object = dfvfs_text_file.TextFile(file_object, encoding='utf-8')

    system_product = text_file_object.readline()

    # Only parse known default /etc/issue file contents.
    if system_product.startswith('Debian GNU/Linux '):
      system_product, _, _ = system_product.partition('\\')
      system_product = system_product.rstrip()

    else:
      system_product = None

    if system_product:
      mediator.SetValue('operating_system_product', system_product)


class LinuxStandardBaseReleasePlugin(interface.FileArtifactPreprocessorPlugin):
  """The Linux standard base (LSB) release plugin."""

  ARTIFACT_DEFINITION_NAME = 'LinuxLSBRelease'

  def _ParseFileData(self, mediator, file_object):
    """Parses file content (data) for system product preprocessing attribute.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.
      file_object (dfvfs.FileIO): file-like object that contains the artifact
          value data.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    text_file_object = dfvfs_text_file.TextFile(file_object, encoding='utf-8')

    product_values = {}
    for line in text_file_object.readlines():
      line = line.strip()
      if line.startswith('#'):
        continue
      key, value = line.split('=')
      key = key.strip().upper()
      value = value.strip().strip('"')
      product_values[key] = value

    system_product = product_values.get('DISTRIB_DESCRIPTION', None)
    if system_product:
      mediator.SetValue('operating_system_product', system_product)


class LinuxSystemdOperatingSystemPlugin(
    interface.FileArtifactPreprocessorPlugin):
  """The Linux systemd operating system release plugin."""

  ARTIFACT_DEFINITION_NAME = 'LinuxSystemdOSRelease'

  def _ParseFileData(self, mediator, file_object):
    """Parses file content (data) for system product preprocessing attribute.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.
      file_object (dfvfs.FileIO): file-like object that contains the artifact
          value data.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    text_file_object = dfvfs_text_file.TextFile(file_object, encoding='utf-8')

    product_values = {}
    for line in text_file_object.readlines():
      line = line.strip()

      # Ignore lines that do not define a key value pair.
      if '=' not in line:
        continue

      key, value = line.split('=')
      key = key.upper()
      value = value.strip('"')
      product_values[key] = value

    system_product = product_values.get('PRETTY_NAME', None)
    if system_product:
      mediator.SetValue('operating_system_product', system_product)


class LinuxTimeZonePlugin(interface.FileEntryArtifactPreprocessorPlugin):
  """Linux time zone plugin."""

  ARTIFACT_DEFINITION_NAME = 'LinuxLocalTime'

  def _ParseFileEntry(self, mediator, file_entry):
    """Parses artifact file system data for a preprocessing attribute.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.
      file_entry (dfvfs.FileEntry): file entry that contains the artifact
          value data.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    if file_entry.link:
      # Determine the timezone based on the file path.
      _, _, time_zone = file_entry.link.partition('zoneinfo/')

    else:
      # Determine the timezone based on the timezone information file.
      file_object = file_entry.GetFileObject()

      time_zone = None
      try:
        time_zone_file = tz.tzfile(file_object)
        date_time = datetime.datetime(2017, 1, 1)
        time_zone = time_zone_file.tzname(date_time)

      except ValueError:
        mediator.ProducePreprocessingWarning(
            self.ARTIFACT_DEFINITION_NAME,
            'Unable to read time zone information file.')

    if time_zone:
      try:
        mediator.SetTimeZone(time_zone)
      except ValueError:
        mediator.ProducePreprocessingWarning(
            self.ARTIFACT_DEFINITION_NAME,
            'Unable to set time zone in knowledge base.')


class LinuxUserAccountsPlugin(interface.FileArtifactPreprocessorPlugin):
  """The Linux user accounts plugin."""

  ARTIFACT_DEFINITION_NAME = 'LinuxPasswdFile'

  def _ParseFileData(self, mediator, file_object):
    """Parses file content (data) for user account preprocessing attributes.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.
      file_object (dfvfs.FileIO): file-like object that contains the artifact
          value data.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    line_reader = line_reader_file.BinaryLineReader(file_object)

    try:
      reader = line_reader_file.BinaryDSVReader(line_reader, b':')
    except csv.Error as exception:
      raise errors.PreProcessFail(
          'Unable to read: {0:s} with error: {1!s}'.format(
              self.ARTIFACT_DEFINITION_NAME, exception))

    for line_number, row in enumerate(reader):
      if len(row) < 7 or not row[0] or not row[2]:
        mediator.ProducePreprocessingWarning(
            self.ARTIFACT_DEFINITION_NAME,
            'Unsupported number of values in line: {0:d}.'.format(line_number))
        continue

      try:
        username = row[0].decode('utf-8')
      except UnicodeDecodeError:
        mediator.ProducePreprocessingWarning(
            self.ARTIFACT_DEFINITION_NAME, 'Unable to decode username.')
        continue

      try:
        identifier = row[2].decode('utf-8')
      except UnicodeDecodeError:
        mediator.ProducePreprocessingWarning(
            self.ARTIFACT_DEFINITION_NAME, 'Unable to decode user identifier.')
        continue

      group_identifier = None
      if row[3]:
        try:
          group_identifier = row[3].decode('utf-8')
        except UnicodeDecodeError:
          mediator.ProducePreprocessingWarning(
              self.ARTIFACT_DEFINITION_NAME,
              'Unable to decode group identifier.')

      full_name = None
      if row[4]:
        try:
          full_name = row[4].decode('utf-8')
        except UnicodeDecodeError:
          mediator.ProducePreprocessingWarning(
              self.ARTIFACT_DEFINITION_NAME, 'Unable to decode full name.')

      user_directory = None
      if row[5]:
        try:
          user_directory = row[5].decode('utf-8')
        except UnicodeDecodeError:
          mediator.ProducePreprocessingWarning(
              self.ARTIFACT_DEFINITION_NAME, 'Unable to decode user directory.')

      shell = None
      if row[6]:
        try:
          shell = row[6].decode('utf-8')
        except UnicodeDecodeError:
          mediator.ProducePreprocessingWarning(
              self.ARTIFACT_DEFINITION_NAME, 'Unable to decode shell.')

      user_account = artifacts.UserAccountArtifact(
          identifier=identifier, username=username)
      user_account.group_identifier = group_identifier
      user_account.full_name = full_name
      user_account.user_directory = user_directory
      user_account.shell = shell

      try:
        mediator.AddUserAccount(user_account)
      except KeyError as exception:
        mediator.ProducePreprocessingWarning(
            self.ARTIFACT_DEFINITION_NAME,
            'Unable to add user account with error: {0!s}'.format(exception))


manager.PreprocessPluginsManager.RegisterPlugins([
    LinuxHostnamePlugin, LinuxDistributionPlugin, LinuxIssueFilePlugin,
    LinuxStandardBaseReleasePlugin, LinuxSystemdOperatingSystemPlugin,
    LinuxTimeZonePlugin, LinuxUserAccountsPlugin])
