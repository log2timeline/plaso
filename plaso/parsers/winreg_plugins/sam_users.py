# -*- coding: utf-8 -*-
""""Windows Registry plugin for SAM Users Account information."""

import os

from dfdatetime import filetime as dfdatetime_filetime

from plaso.containers import events
from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.parsers import winreg_parser
from plaso.parsers.winreg_plugins import interface


class SAMUsersWindowsRegistryEventData(events.EventData):
  """Class that defines SAM users Windows Registry event data.

  Attributes:
    account_rid (int): account relative identifier (RID).
    comments (str): comments.
    fullname (str): full name.
    key_path (str): Windows Registry key path.
    last_login_time (dfdatetime.DateTimeValues): date and time of the last
       login.
    last_password_set_time (dfdatetime.DateTimeValues): date and time of the
        last password set.
    last_written_time (dfdatetime.DateTimeValues): entry last written date and
        time.
    login_count (int): login count.
    username (str): a string containing the username.
  """

  DATA_TYPE = 'windows:registry:sam_users'

  def __init__(self):
    """Initializes event data."""
    super(SAMUsersWindowsRegistryEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.account_rid = None
    self.comments = None
    self.fullname = None
    self.key_path = None
    self.last_login_time = None
    self.last_password_set_time = None
    self.last_written_time = None
    self.login_count = None
    self.username = None


class SAMUsersWindowsRegistryPlugin(
    interface.WindowsRegistryPlugin, dtfabric_helper.DtFabricHelper):
  """Windows Registry plugin for SAM Users Account information."""

  NAME = 'windows_sam_users'
  DATA_FORMAT = 'Security Accounts Manager (SAM) users Registry data'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_LOCAL_MACHINE\\SAM\\SAM\\Domains\\Account\\Users')])

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'sam_users.yaml')

  _V_VALUE_STRINGS_OFFSET = 0xcc

  def _ParseFValue(self, registry_key):
    """Parses an F value.

    Args:
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.

    Returns:
      f_value: F value stored in the Windows Registry key.

    Raises:
      ParseError: if the Windows Registry key does not contain an F value or
          F value cannot be parsed.
    """
    registry_value = registry_key.GetValueByName('F')
    if not registry_value:
      raise errors.ParseError(
          'missing value: "F" in Windows Registry key: {0:s}.'.format(
              registry_key.name))

    f_value_map = self._GetDataTypeMap('f_value')

    try:
      return self._ReadStructureFromByteStream(
          registry_value.data, 0, f_value_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError(exception)

  def _ParseVValueString(
      self, parser_mediator, data, user_information_descriptor):
    """Parses a V value string.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      data (bytes): Windows Registry V value data.
      user_information_descriptor (user_information_descriptor): V value
          user information descriptor.

    Returns:
      str: string value stored in the Windows Registry V value data.
    """
    data_start_offset = (
        user_information_descriptor.offset + self._V_VALUE_STRINGS_OFFSET)
    data_end_offset = data_start_offset + user_information_descriptor.size
    descriptor_data = data[data_start_offset:data_end_offset]

    try:
      username = descriptor_data.decode('utf-16-le')
    except (UnicodeDecodeError, UnicodeEncodeError) as exception:
      username = descriptor_data.decode('utf-16-le', errors='replace')
      parser_mediator.ProduceExtractionWarning((
          'unable to decode V value string with error: {0!s}. Characters '
          'that cannot be decoded will be replaced with "?" or '
          '"\\ufffd".').format(exception))

    return username

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    names_key = registry_key.GetSubkeyByName('Names')
    if not names_key:
      parser_mediator.ProduceExtractionWarning('missing subkey: Names.')
      return

    last_written_time_per_username = {
        name_key.name: name_key.last_written_time
        for name_key in names_key.GetSubkeys()}

    for subkey in registry_key.GetSubkeys():
      if subkey.name == 'Names':
        continue

      try:
        f_value = self._ParseFValue(subkey)
      except errors.ParseError as exception:
        parser_mediator.ProduceExtractionWarning(
            'unable to parse F value with error: {0!s}'.format(exception))
        continue

      registry_value = subkey.GetValueByName('V')
      if not registry_value:
        parser_mediator.ProduceExtractionWarning(
            'missing Registry value: "V" in subkey: {0:s}.'.format(
                subkey.name))
        continue

      v_value_map = self._GetDataTypeMap('v_value')

      try:
        v_value = self._ReadStructureFromByteStream(
            registry_value.data, 0, v_value_map)
      except (ValueError, errors.ParseError) as exception:
        parser_mediator.ProduceExtractionWarning(
            'unable to parse V value with error: {0!s}'.format(exception))
        continue

      username = self._ParseVValueString(
          parser_mediator, registry_value.data, v_value[1])

      # TODO: check if subkey.name == f_value.rid

      event_data = SAMUsersWindowsRegistryEventData()
      event_data.account_rid = f_value.rid
      event_data.comments = self._ParseVValueString(
          parser_mediator, registry_value.data, v_value[3])
      event_data.fullname = self._ParseVValueString(
          parser_mediator, registry_value.data, v_value[2])
      event_data.key_path = registry_key.path
      event_data.last_written_time = last_written_time_per_username.get(
          username, None)
      event_data.login_count = f_value.number_of_logons
      event_data.username = username

      if f_value.last_login_time:
        event_data.last_login_time = dfdatetime_filetime.Filetime(
            timestamp=f_value.last_login_time)

      if f_value.last_password_set_time:
        event_data.last_password_set_time = dfdatetime_filetime.Filetime(
            timestamp=f_value.last_password_set_time)

      parser_mediator.ProduceEventData(event_data)


winreg_parser.WinRegistryParser.RegisterPlugin(SAMUsersWindowsRegistryPlugin)
