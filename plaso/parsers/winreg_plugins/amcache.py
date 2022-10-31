# -*- coding: utf-8 -*-
"""Windows Registry plugin to parse the AMCache.hve Root key."""

import re

from dfdatetime import filetime as dfdatetime_filetime
from dfdatetime import posix_time as dfdatetime_posix_time
from dfdatetime import time_elements as dfdatetime_time_elements

from dfwinreg import errors as dfwinreg_errors

from plaso.containers import events
from plaso.parsers import winreg_parser
from plaso.parsers.winreg_plugins import interface


class AMCacheFileEventData(events.EventData):
  """AMCache file event data.

  Attributes:
    company_name (str): company name that created product file belongs to.
    file_creation_time (dfdatetime.DateTimeValues): file entry creation date
        and time.
    file_description (str): description of file.
    file_modification_time (dfdatetime.DateTimeValues): file entry last
        modification date and time.
    file_reference (str): file system file reference, for example 9-1 (MFT
        entry - sequence number).
    file_size (int): size of file in bytes.
    file_version (str): version of file.
    full_path (str): full path of file.
    installation_time (dfdatetime.DateTimeValues): installation date and time.
    language_code (int): language code of file.
    last_written_time (dfdatetime.DateTimeValues): entry last written date and
        time.
    link_time (dfdatetime.DateTimeValues): link date and time.
    msi_installation_time (dfdatetime.DateTimeValues): MSI installation date
        and time.
    product_name (str): product name file belongs to.
    program_identifier (str): GUID of entry under Root/Program key file belongs
        to.
    sha1 (str): SHA-1.
  """

  DATA_TYPE = 'windows:registry:amcache'

  def __init__(self):
    """Initializes event data."""
    super(AMCacheFileEventData, self).__init__(data_type=self.DATA_TYPE)
    self.company_name = None
    self.file_creation_time = None
    self.file_description = None
    self.file_modification_time = None
    self.file_reference = None
    self.file_size = None
    self.file_version = None
    self.full_path = None
    self.installation_time = None
    self.language_code = None
    self.last_written_time = None
    self.link_time = None
    self.msi_installation_time = None
    self.product_name = None
    self.program_identifier = None
    self.sha1 = None


class AMCacheProgramEventData(events.EventData):
  """AMCache programs event data.

  Attributes:
    entry_type (str): type of entry (usually AddRemoveProgram).
    file_paths (str): file paths of installed program.
    files (str): list of files belonging to program.
    installation_time (dfdatetime.DateTimeValues): installation date and time.
    language_code (int): language_code of program.
    msi_package_code (str): MSI package code of program.
    msi_product_code (str): MSI product code of program.
    name (str): name of installed program.
    package_code (str): package code of program.
    product_code (str): product code of program.
    publisher (str): publisher of program.
    uninstall_key (str): unicode string of uninstall registry key for program.
    version (str): version of program.
  """

  DATA_TYPE = 'windows:registry:amcache:programs'

  def __init__(self):
    """Initializes event data."""
    super(AMCacheProgramEventData, self).__init__(data_type=self.DATA_TYPE)
    self.entry_type = None
    self.file_paths = None
    self.files = None
    self.installation_time = None
    self.language_code = None
    self.msi_package_code = None
    self.msi_product_code = None
    self.name = None
    self.package_code = None
    self.product_code = None
    self.publisher = None
    self.uninstall_key = None
    self.version = None


class AMCachePlugin(interface.WindowsRegistryPlugin):
  """AMCache.hve Windows Registry plugin."""

  NAME = 'amcache'
  DATA_FORMAT = 'AMCache (AMCache.hve)'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter('\\Root')])

  # Contains: {value name: attribute name}
  _APPLICATION_SUB_KEY_VALUES = {
      'LowerCaseLongPath': 'full_path',
      'ProductName': 'product_name',
      'ProductVersion': 'file_version',
      'ProgramId': 'program_identifier',
      'Publisher': 'company_name',
      'Size': 'file_size'}

  _FILE_REFERENCE_KEY_VALUES = {
      '0': 'product_name',
      '1': 'company_name',
      '3': 'language_code',
      '5': 'file_version',
      '6': 'file_size',
      'c': 'file_description',
      '15': 'full_path',
      '100': 'program_identifier',
      '101': 'sha1'}

  _AMCACHE_LINK_TIME = 'f'
  _AMCACHE_FILE_MODIFICATION_TIME = '11'
  _AMCACHE_FILE_CREATION_TIME = '12'
  _AMCACHE_ENTRY_WRITE_TIME = '17'

  _AMCACHE_P_INSTALLATION_TIME = 'a'

  _AMCACHE_P_FILES = 'Files'

  # Date and time string formatted as: "MM/DD/YYYY hh:mm:ss"
  # for example "04/07/2014 15:18:49"
  # TODO: determine if this is true for other locales.
  _LINK_DATE_TIME_RE = re.compile(
      r'([0-9][0-9])/([0-9][0-9])/([0-9][0-9][0-9][0-9]) '
      r'([0-9][0-9]):([0-9][0-9]):([0-9][0-9])')

  _PRODUCT_KEY_VALUES = {
      '0': 'name',
      '1': 'version',
      '2': 'publisher',
      '3': 'language_code',
      '6': 'entry_type',
      '7': 'uninstall_key',
      'd': 'file_paths',
      'f': 'product_code',
      '10': 'package_code',
      '11': 'msi_product_code',
      '12': 'msi_package_code'}

  def _GetValueDataAsObject(
      self, parser_mediator, key_path, value_name, registry_value):
    """Retrieves the value data as an object from a Windows Registry value.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      key_path (str): key path.
      value_name (str): name of the value.
      registry_value (dfwinreg.WinRegistryValue): Windows Registry value.

    Returns:
      object: value data or None when the value data cannot be determined.
    """
    if registry_value.data is None:
      return '(empty)'

    try:
      value_object = registry_value.GetDataAsObject()

      if registry_value.DataIsMultiString():
        value_object = list(value_object)

      elif (not registry_value.DataIsInteger() and
            not registry_value.DataIsString()):
        # Represent remaining types like REG_BINARY and
        # REG_RESOURCE_REQUIREMENT_LIST.
        value_object = registry_value.data

    except dfwinreg_errors.WinRegistryValueError as exception:
      parser_mediator.ProduceRecoveryWarning((
          'Unable to retrieve value data of type: {0:s} as object from '
          'value: {1:s} in key: {2:s} with error: {3!s}').format(
              registry_value.data_type_string, value_name, key_path, exception))
      value_object = None

    return value_object

  def _ParseApplicationSubKey(self, parser_mediator, application_sub_key):
    """Parses a Root\\InventoryApplicationFile\\%NAME%|%IDENTIFIER% key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      application_sub_key (dfwinreg.WinRegistryKey): application sub key of the
          InventoryApplicationFile Windows Registry key.
    """
    event_data = AMCacheFileEventData()

    for value_name, attribute_name in self._APPLICATION_SUB_KEY_VALUES.items():
      value = application_sub_key.GetValueByName(value_name)
      if value:
        value_data = self._GetValueDataAsObject(
            parser_mediator, application_sub_key.path, value_name, value)

        setattr(event_data, attribute_name, value_data)

    install_date_value = application_sub_key.GetValueByName('InstallDate')
    if install_date_value:
      event_data.installation_time = self._ParseDateStringValue(
          parser_mediator, application_sub_key.path, install_date_value)

    install_date_msi_value = application_sub_key.GetValueByName(
        'InstallDateMsi')
    if install_date_msi_value:
      event_data.msi_installation_time = self._ParseDateStringValue(
          parser_mediator, application_sub_key.path, install_date_msi_value)

    link_date_value = application_sub_key.GetValueByName('LinkDate')
    if link_date_value:
      event_data.link_time = self._ParseDateStringValue(
          parser_mediator, application_sub_key.path, link_date_value)

    parser_mediator.ProduceEventData(event_data)

  def _ParseDateStringValue(self, parser_mediator, key_path, registry_value):
    """Parses a date and time string value.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      key_path (str): key path.
      registry_value (dfwinreg.WinRegistryValue): Windows Registry value.

    Returns:
      dfdatetime_time_elements.TimeElements: date and time value or None
          if not available.
    """
    if not registry_value.DataIsString():
      parser_mediator.ProduceExtractionWarning((
          'unsupported {0:s} with value data type: {1:s} in key: '
          '{2:s}').format(
              registry_value.name, registry_value.data_type_string, key_path))
      return None

    date_time_string = registry_value.GetDataAsObject()
    if not date_time_string:
      parser_mediator.ProduceExtractionWarning(
          'missing {0:s} value data in key: {1:s}'.format(
              registry_value.name, key_path))
      return None

    re_match = self._LINK_DATE_TIME_RE.match(date_time_string)
    if not re_match:
      parser_mediator.ProduceExtractionWarning(
          'unsupported {0:s} value data: {1!s} in key: {2:s}'.format(
              registry_value.name, date_time_string, key_path))
      return None

    month, day_of_month, year, hours, minutes, seconds= re_match.groups()

    try:
      year = int(year, 10)
      month = int(month, 10)
      day_of_month = int(day_of_month, 10)
      hours = int(hours, 10)
      minutes = int(minutes, 10)
      seconds = int(seconds, 10)
    except (TypeError, ValueError):
      parser_mediator.ProduceExtractionWarning(
          'invalid {0:s} date time value: {1!s} in key: {2:s}'.format(
              registry_value.name, date_time_string, key_path))
      return None

    time_elements_tuple = (year, month, day_of_month, hours, minutes, seconds)

    try:
      date_time = dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple)
    except ValueError:
      parser_mediator.ProduceExtractionWarning(
          'invalid {0:s} date time value: {1!s} in key: {2:s}'.format(
              registry_value.name, time_elements_tuple, key_path))
      return None

    return date_time

  def _ParseFileKey(self, parser_mediator, file_key):
    """Parses a Root\\File key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_key (dfwinreg.WinRegistryKey): the File Windows Registry key.
    """
    for volume_key in file_key.GetSubkeys():
      for file_reference_key in volume_key.GetSubkeys():
        self._ParseFileReferenceKey(parser_mediator, file_reference_key)

  def _ParseFileReferenceKey(self, parser_mediator, file_reference_key):
    """Parses a file reference key (sub key of Root\\File\\%VOLUME%) for events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_reference_key (dfwinreg.WinRegistryKey): file reference Windows
          Registry key.
    """
    event_data = AMCacheFileEventData()

    try:
      if '0000' in file_reference_key.name:
        # A NTFS file reference is a combination of MFT entry and sequence
        # number.
        sequence_number, mft_entry = file_reference_key.name.split('0000')
        mft_entry = int(mft_entry, 16)
        sequence_number = int(sequence_number, 16)
        event_data.file_reference = '{0:d}-{1:d}'.format(
            mft_entry, sequence_number)
      else:
        # A FAT file reference is the offset of the corresponding directory
        # entry.
        file_reference = int(file_reference_key.name, 16)
        event_data.file_reference = '{0:d}'.format(file_reference)

    except (ValueError, TypeError):
      pass

    for value_name, attribute_name in self._FILE_REFERENCE_KEY_VALUES.items():
      value = file_reference_key.GetValueByName(value_name)
      if not value:
        continue

      value_data = self._GetValueDataAsObject(
          parser_mediator, file_reference_key.path, value_name, value)

      if attribute_name == 'sha1' and value_data.startswith('0000'):
        # Strip off the 4 leading zero's from the sha1 hash.
        value_data = value_data[4:]

      setattr(event_data, attribute_name, value_data)

    write_time_value = file_reference_key.GetValueByName(
        self._AMCACHE_ENTRY_WRITE_TIME)
    if write_time_value:
      timestamp = write_time_value.GetDataAsObject()
      event_data.last_written_time = dfdatetime_filetime.Filetime(
          timestamp=timestamp)

    creation_time_value = file_reference_key.GetValueByName(
        self._AMCACHE_FILE_CREATION_TIME)
    if creation_time_value:
      timestamp = creation_time_value.GetDataAsObject()
      event_data.file_creation_time = dfdatetime_filetime.Filetime(
          timestamp=timestamp)

    modification_time_value = file_reference_key.GetValueByName(
        self._AMCACHE_FILE_MODIFICATION_TIME)
    if modification_time_value:
      timestamp = modification_time_value.GetDataAsObject()
      event_data.file_modification_time = dfdatetime_filetime.Filetime(
          timestamp=timestamp)

    link_time_value = file_reference_key.GetValueByName(self._AMCACHE_LINK_TIME)
    if link_time_value:
      timestamp = link_time_value.GetDataAsObject()
      event_data.link_time = dfdatetime_posix_time.PosixTime(
          timestamp=timestamp)

    parser_mediator.ProduceEventData(event_data)

  def _ParseInventoryApplicationFileKey(
      self, parser_mediator, inventory_application_file_key):
    """Parses a Root\\InventoryApplicationFile key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      inventory_application_file_key (dfwinreg.WinRegistryKey): the
          InventoryApplicationFile Windows Registry key.
    """
    for application_sub_key in inventory_application_file_key.GetSubkeys():
      self._ParseApplicationSubKey(parser_mediator, application_sub_key)

  def _ParseProgramKey(self, parser_mediator, program_key):
    """Parses a program key (a sub key of Root\\Programs) for events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      program_key (dfwinreg.WinRegistryKey): program Windows Registry key.
    """
    event_data = AMCacheProgramEventData()

    for value_name, attribute_name in self._PRODUCT_KEY_VALUES.items():
      value = program_key.GetValueByName(value_name)
      if value:
        value_data = self._GetValueDataAsObject(
            parser_mediator, program_key.path, value_name, value)

        setattr(event_data, attribute_name, value_data)

    installation_time_value = program_key.GetValueByName(
        self._AMCACHE_P_INSTALLATION_TIME)
    if installation_time_value:
      timestamp = installation_time_value.GetDataAsObject()
      event_data.installation_time = dfdatetime_posix_time.PosixTime(
          timestamp=timestamp)

    parser_mediator.ProduceEventData(event_data)

  def _ParseProgramsKey(self, parser_mediator, programs_key):
    """Parses a Root\\Programs key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      programs_key (dfwinreg.WinRegistryKey): the Programs Windows Registry key.
    """
    for program_key in programs_key.GetSubkeys():
      self._ParseProgramKey(parser_mediator, program_key)

  def _ParseRootKey(self, parser_mediator, root_key):
    """Parses a Root key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      root_key (dfwinreg.WinRegistryKey): the Root Windows Registry key.
    """
    self._ProduceDefaultWindowsRegistryEvent(parser_mediator, root_key)

    for sub_key in root_key.GetSubkeys():
      self._ParseSubKey(parser_mediator, sub_key)

      if sub_key.name == 'File':
        self._ParseFileKey(parser_mediator, sub_key)

      elif sub_key.name == 'InventoryApplicationFile':
        self._ParseInventoryApplicationFileKey(parser_mediator, sub_key)

      elif sub_key.name == 'Programs':
        self._ParseProgramsKey(parser_mediator, sub_key)

  def _ParseSubKey(self, parser_mediator, registry_key):
    """Parses a sub key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): the Windows Registry key.
    """
    self._ProduceDefaultWindowsRegistryEvent(parser_mediator, registry_key)

    for sub_key in registry_key.GetSubkeys():
      self._ParseSubKey(parser_mediator, sub_key)

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    self._ParseRootKey(parser_mediator, registry_key)


winreg_parser.WinRegistryParser.RegisterPlugin(AMCachePlugin)
