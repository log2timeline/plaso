# -*- coding: utf-8 -*-
"""Windows Registry plugin to parse the AMCache.hve Root key."""

from dfdatetime import filetime as dfdatetime_filetime
from dfdatetime import posix_time as dfdatetime_posix_time

from dfwinreg import errors as dfwinreg_errors

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import winreg_parser
from plaso.parsers.winreg_plugins import interface


class AMCacheFileEventData(events.EventData):
  """AMCache file event data.

  Attributes:
    company_name (str): company name that created product file belongs to.
    file_description (str): description of file.
    file_reference (str): file system file reference, for example 9-1 (MFT
        entry - sequence number).
    file_size (int): size of file in bytes.
    file_version (str): version of file.
    full_path (str): full path of file.
    language_code (int): language code of file.
    product_name (str): product name file belongs to.
    program_identifier (str): GUID of entry under Root/Program key file belongs
        to.
    sha1 (str): SHA-1 of file.
  """

  DATA_TYPE = 'windows:registry:amcache'

  def __init__(self):
    """Initializes event data."""
    super(AMCacheFileEventData, self).__init__(data_type=self.DATA_TYPE)
    self.company_name = None
    self.file_description = None
    self.file_reference = None
    self.file_size = None
    self.file_version = None
    self.full_path = None
    self.language_code = None
    self.product_name = None
    self.program_identifier = None
    self.sha1 = None


class AMCacheProgramEventData(events.EventData):
  """AMCache programs event data.

  Attributes:
    entry_type (str): type of entry (usually AddRemoveProgram).
    file_paths (str): file paths of installed program.
    files (str): list of files belonging to program.
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

  _AMCACHE_COMPILATION_TIME = 'f'
  _AMCACHE_FILE_MODIFICATION_TIME = '11'
  _AMCACHE_FILE_CREATION_TIME = '12'
  _AMCACHE_ENTRY_WRITE_TIME = '17'

  _AMCACHE_P_INSTALLATION_TIME = 'a'

  _AMCACHE_P_FILES = 'Files'

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
      '12': 'msi_package_code',
  }

  def _GetValueDataAsObject(
      self, parser_mediator, key_path, value_name, registry_value):
    """Retrieves the value data as an object from a Windows Registry value.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
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
        # A NTFS file is a combination of MFT entry and sequence number.
        sequence_number, mft_entry = file_reference_key.name.split('0000')
        mft_entry = int(mft_entry, 16)
        sequence_number = int(sequence_number, 16)
        event_data.file_reference = '{0:d}-{1:d}'.format(
            mft_entry, sequence_number)
      else:
        # A FAT file is a single number.
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

    amcache_time_value = file_reference_key.GetValueByName(
        self._AMCACHE_ENTRY_WRITE_TIME)
    if amcache_time_value:
      timestamp = amcache_time_value.GetDataAsObject()
      amcache_time = dfdatetime_filetime.Filetime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          amcache_time, definitions.TIME_DESCRIPTION_MODIFICATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    creation_time_value = file_reference_key.GetValueByName(
        self._AMCACHE_FILE_CREATION_TIME)
    if creation_time_value:
      timestamp = creation_time_value.GetDataAsObject()
      creation_time = dfdatetime_filetime.Filetime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          creation_time, definitions.TIME_DESCRIPTION_CREATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    modification_time_value = file_reference_key.GetValueByName(
        self._AMCACHE_FILE_MODIFICATION_TIME)
    if modification_time_value:
      timestamp = modification_time_value.GetDataAsObject()
      modification_time = dfdatetime_filetime.Filetime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          modification_time, definitions.TIME_DESCRIPTION_MODIFICATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    compilation_time_value = file_reference_key.GetValueByName(
        self._AMCACHE_COMPILATION_TIME)
    if compilation_time_value:
      timestamp = compilation_time_value.GetDataAsObject()
      link_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          link_time, definitions.TIME_DESCRIPTION_CHANGE)
      parser_mediator.ProduceEventWithEventData(event, event_data)

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
      if not value:
        continue

      value_data = self._GetValueDataAsObject(
          parser_mediator, program_key.path, value_name, value)

      setattr(event_data, attribute_name, value_data)

    installation_time_value = program_key.GetValueByName(
        self._AMCACHE_P_INSTALLATION_TIME)
    if installation_time_value:
      timestamp = installation_time_value.GetDataAsObject()
      installation_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          installation_time, definitions.TIME_DESCRIPTION_INSTALLATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

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
