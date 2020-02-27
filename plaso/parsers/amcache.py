# -*- coding: utf-8 -*-
"""File containing a Windows Registry plugin to parse the AMCache.hve file."""

from __future__ import unicode_literals

import pyregf

from dfdatetime import filetime
from dfdatetime import posix_time
from dfwinreg import definitions as dfwinreg_definitions
from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import interface
from plaso.parsers import manager


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

class AMCacheParser(interface.FileObjectParser):
  """AMCache Registry plugin for recently run programs."""

  NAME = 'amcache'
  DESCRIPTION = 'Parser for AMCache Registry entries.'

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

  #TODO Add GetFormatSpecification when issues are fixed with adding
  #     multiple parsers for the same file format (in this case regf files)
  #     AddNewSignature ->
  #     b'\x41\x00\x6d\x00\x63\x00\x61\x00\x63\x00\x68\x00\x65', offset=88

  def _GetValueDataAsObject(self, parser_mediator, value):
    """Retrieves the value data as an object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      value (pyregf_value): value.

    Returns:
      object: data as a Python type or None if the value cannot be read.
    """
    try:
      if value.type in (
          dfwinreg_definitions.REG_SZ,
          dfwinreg_definitions.REG_EXPAND_SZ,
          dfwinreg_definitions.REG_LINK):
        value_data = value.get_data_as_string()

      elif value.type in (
          dfwinreg_definitions.REG_DWORD,
          dfwinreg_definitions.REG_DWORD_BIG_ENDIAN,
          dfwinreg_definitions.REG_QWORD):
        value_data = value.get_data_as_integer()

      elif value.type == dfwinreg_definitions.REG_MULTI_SZ:
        value_data = list(value.get_data_as_multi_string())

      else:
        value_data = value.data

    except (IOError, OverflowError) as exception:
      parser_mediator.ProduceExtractionWarning(
          'Unable to read data from value: {0:s} with error: {1!s}'.format(
              value.name, exception))
      return None

    return value_data

  def _ParseFileKey(self, parser_mediator, file_key):
    """Parses a Root\\File key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_key (pyregf.key): the File key.
    """
    for volume_key in file_key.sub_keys:
      for file_reference_key in volume_key.sub_keys:
        self._ParseFileReferenceKey(parser_mediator, file_reference_key)

  def _ParseFileReferenceKey(self, parser_mediator, file_reference_key):
    """Parses a file reference key (sub key of Root\\File\\%VOLUME%) for events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_reference_key (pyregf.key): file reference key.
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
      value = file_reference_key.get_value_by_name(value_name)
      if not value:
        continue

      value_data = self._GetValueDataAsObject(parser_mediator, value)
      if attribute_name == 'sha1' and value_data.startswith('0000'):
        # Strip off the 4 leading zero's from the sha1 hash.
        value_data = value_data[4:]

      setattr(event_data, attribute_name, value_data)

    amcache_time_value = file_reference_key.get_value_by_name(
        self._AMCACHE_ENTRY_WRITE_TIME)
    if amcache_time_value:
      amcache_time = filetime.Filetime(amcache_time_value.get_data_as_integer())
      event = time_events.DateTimeValuesEvent(
          amcache_time, definitions.TIME_DESCRIPTION_MODIFICATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    creation_time_value = file_reference_key.get_value_by_name(
        self._AMCACHE_FILE_CREATION_TIME)
    if creation_time_value:
      creation_time = filetime.Filetime(
          creation_time_value.get_data_as_integer())
      event = time_events.DateTimeValuesEvent(
          creation_time, definitions.TIME_DESCRIPTION_CREATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    modification_time_value = file_reference_key.get_value_by_name(
        self._AMCACHE_FILE_MODIFICATION_TIME)
    if modification_time_value:
      modification_time = filetime.Filetime(
          modification_time_value.get_data_as_integer())
      event = time_events.DateTimeValuesEvent(
          modification_time, definitions.TIME_DESCRIPTION_MODIFICATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    compilation_time_value = file_reference_key.get_value_by_name(
        self._AMCACHE_COMPILATION_TIME)
    if compilation_time_value:
      link_time = posix_time.PosixTime(
          compilation_time_value.get_data_as_integer())
      event = time_events.DateTimeValuesEvent(
          link_time, definitions.TIME_DESCRIPTION_CHANGE)
      parser_mediator.ProduceEventWithEventData(event, event_data)

  def _ParseProgramKey(self, parser_mediator, program_key):
    """Parses a program key (a sub key of Root\\Programs) for events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      program_key (pyregf_key): program key.
    """
    event_data = AMCacheProgramEventData()

    for value_name, attribute_name in self._PRODUCT_KEY_VALUES.items():
      value = program_key.get_value_by_name(value_name)
      if not value:
        continue

      value_data = self._GetValueDataAsObject(parser_mediator, value)
      setattr(event_data, attribute_name, value_data)

    installation_time_value = program_key.get_value_by_name(
        self._AMCACHE_P_INSTALLATION_TIME)
    if installation_time_value:
      installation_time = posix_time.PosixTime(
          installation_time_value.get_data_as_integer())
      event = time_events.DateTimeValuesEvent(
          installation_time, definitions.TIME_DESCRIPTION_INSTALLATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

  def _ParseProgramsKey(self, parser_mediator, programs_key):
    """Parses a Root\\Programs key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      programs_key (pyregf.key): the Programs key.
    """
    for program_key in programs_key.sub_keys:
      self._ParseProgramKey(parser_mediator, program_key)

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses an AMCache.hve file-like object for events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.
    """
    regf_file = pyregf.file()
    try:
      regf_file.open_file_object(file_object)
    except IOError:
      # The error is currently ignored -> see TODO above related to the
      # fixing of handling multiple parsers for the same file format.
      return

    root_key = regf_file.get_key_by_path('Root')
    if root_key:
      file_key = root_key.get_sub_key_by_path('File')
      if file_key:
        self._ParseFileKey(parser_mediator, file_key)

      programs_key = root_key.get_sub_key_by_path('Programs')
      if programs_key:
        self._ParseProgramsKey(parser_mediator, programs_key)

    regf_file.close()


manager.ParsersManager.RegisterParser(AMCacheParser)
