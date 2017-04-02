# -*- coding: utf-8 -*-
""""Windows Registry plugin for SAM Users Account information."""

import construct

from dfdatetime import filetime as dfdatetime_filetime

from plaso.containers import events
from plaso.containers import time_events
from plaso.containers import windows_events
from plaso.lib import definitions
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


__author__ = 'Preston Miller, dpmforensics.com, github.com/prmiller91'


class SAMUsersWindowsRegistryEventData(events.EventData):
  """Class that defines SAM users Windows Registry event data.

  Attributes:
    account_rid (int): account relative identifier (RID).
    comments (str): comments.
    fullname (str): full name.
    key_path (str): Windows Registry key path.
    login_count (int): login count.
    username (str): a string containing the username.
  """
  DATA_TYPE = u'windows:registry:sam_users'

  def __init__(self):
    """Initializes event data."""
    super(SAMUsersWindowsRegistryEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.account_rid = None
    self.comments = None
    self.fullname = None
    self.key_path = None
    self.login_count = None
    self.username = None


class SAMUsersWindowsRegistryPlugin(interface.WindowsRegistryPlugin):
  """Windows Registry plugin for SAM Users Account information."""

  NAME = u'windows_sam_users'
  DESCRIPTION = u'Parser for SAM Users and Names Registry keys.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_LOCAL_MACHINE\\SAM\\Domains\\Account\\Users')])

  _F_VALUE_STRUCT = construct.Struct(
      u'f_struct',
      construct.Padding(8),
      construct.ULInt64(u'last_login'),
      construct.Padding(8),
      construct.ULInt64(u'password_reset'),
      construct.Padding(16),
      construct.ULInt16(u'rid'),
      construct.Padding(16),
      construct.ULInt8(u'login_count'))

  _V_VALUE_HEADER = construct.Struct(
      u'v_header',
      construct.Array(11, construct.ULInt32(u'values')))

  _V_VALUE_STRINGS_OFFSET = 204

  _SOURCE_APPEND = u': User Account Information'

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    names_key = registry_key.GetSubkeyByName(u'Names')
    if not names_key:
      parser_mediator.ProduceExtractionError(u'missing subkey: Names.')
      return

    last_written_time_per_username = {
        registry_value.name: registry_value.last_written_time
        for registry_value in names_key.GetSubkeys()}

    for subkey in registry_key.GetSubkeys():
      if subkey.name == u'Names':
        continue

      f_value = subkey.GetValueByName(u'F')
      if not f_value:
        parser_mediator.ProduceExtractionError(
            u'missing Registry value: "F" in subkey: {0:s}.'.format(
                subkey.name))
        continue

      v_value = subkey.GetValueByName(u'V')
      if not v_value:
        parser_mediator.ProduceExtractionError(
            u'missing Registry value: "V" in subkey: {0:s}.'.format(
                subkey.name))
        continue

      try:
        f_data_struct = self._F_VALUE_STRUCT.parse(f_value.data)
      except construct.FieldError as exception:
        parser_mediator.ProduceExtractionError((
            u'unable to parse Registry value: "F" in subkey: {0:s} '
            u'with error: {1:s}.').format(subkey.name, exception))
        continue

      try:
        v_data_struct = self._V_VALUE_HEADER.parse(v_value.data)
      except construct.FieldError as exception:
        parser_mediator.ProduceExtractionError((
            u'unable to parse Registry value: "V" in subkey: {0:s} '
            u'with error: {1:s}.').format(subkey.name, exception))
        continue

      v_header_values = v_data_struct.values()[0]

      data_start_offset = v_header_values[3] + self._V_VALUE_STRINGS_OFFSET
      data_end_offset = v_header_values[4] + data_start_offset
      utf16_stream = v_value.data[data_start_offset:data_end_offset]

      try:
        username = utf16_stream.decode(u'utf-16-le')
      except (UnicodeDecodeError, UnicodeEncodeError) as exception:
        username = utf16_stream.decode(u'utf-16-le', errors=u'replace')
        parser_mediator.ProduceExtractionError((
            u'unable to decode username string with error: {0:s}. Characters '
            u'that cannot be decoded will be replaced with "?" or '
            u'"\\ufffd".').format(exception))

      data_start_offset = v_header_values[6] + self._V_VALUE_STRINGS_OFFSET
      data_end_offset = v_header_values[7] + data_start_offset
      utf16_stream = v_value.data[data_start_offset:data_end_offset]

      try:
        fullname = utf16_stream.decode(u'utf-16-le')
      except (UnicodeDecodeError, UnicodeEncodeError) as exception:
        fullname = utf16_stream.decode(u'utf-16-le', errors=u'replace')
        parser_mediator.ProduceExtractionError((
            u'unable to decode fullname string with error: {0:s}. Characters '
            u'that cannot be decoded will be replaced with "?" or '
            u'"\\ufffd".').format(exception))

      data_start_offset = v_header_values[9] + self._V_VALUE_STRINGS_OFFSET
      data_end_offset = v_header_values[10] + data_start_offset
      utf16_stream = v_value.data[data_start_offset:data_end_offset]

      try:
        comments = utf16_stream.decode(u'utf-16-le')
      except (UnicodeDecodeError, UnicodeEncodeError) as exception:
        comments = utf16_stream.decode(u'utf-16-le', errors=u'replace')
        parser_mediator.ProduceExtractionError((
            u'unable to decode comments string with error: {0:s}. Characters '
            u'that cannot be decoded will be replaced with "?" or '
            u'"\\ufffd".').format(exception))

      last_written_time = last_written_time_per_username.get(username, None)

      # TODO: check if subkey.name == f_data_struct.rid

      if last_written_time:
        values_dict = {
            u'account_rid': f_data_struct.rid,
            u'login_count': f_data_struct.login_count}

        if username:
          values_dict[u'username'] = username
        if fullname:
          values_dict[u'full_name'] = fullname
        if comments:
          values_dict[u'comments'] = comments

        event_data = windows_events.WindowsRegistryEventData()
        event_data.key_path = registry_key.path
        event_data.offset = registry_key.offset
        event_data.regvalue = values_dict
        event_data.source_append = self._SOURCE_APPEND

        event = time_events.DateTimeValuesEvent(
            last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
        parser_mediator.ProduceEventWithEventData(event, event_data)

      event_data = SAMUsersWindowsRegistryEventData()
      event_data.account_rid = f_data_struct.rid
      event_data.comments = comments
      event_data.fullname = fullname
      event_data.key_path = registry_key.path
      event_data.login_count = f_data_struct.login_count
      event_data.offset = f_value.offset
      event_data.username = username

      if f_data_struct.last_login != 0:
        date_time = dfdatetime_filetime.Filetime(
            timestamp=f_data_struct.last_login)
        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_LAST_LOGIN)
        parser_mediator.ProduceEventWithEventData(event, event_data)

      if f_data_struct.password_reset != 0:
        date_time = dfdatetime_filetime.Filetime(
            timestamp=f_data_struct.password_reset)
        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_LAST_PASSWORD_RESET)
        parser_mediator.ProduceEventWithEventData(event, event_data)


winreg.WinRegistryParser.RegisterPlugin(SAMUsersWindowsRegistryPlugin)
