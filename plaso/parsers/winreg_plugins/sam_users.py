# -*- coding: utf-8 -*-
""""Windows Registry plugin for SAM Users Account information."""

import construct

from plaso.containers import time_events
from plaso.containers import windows_events
from plaso.lib import eventdata
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


__author__ = 'Preston Miller, dpmforensics.com, github.com/prmiller91'


class SAMUsersWindowsRegistryEvent(time_events.FiletimeEvent):
  """Convenience class for a SAM users Windows Registry event.

  Attributes:
    account_rid: an integer containing the account relative identifier (RID).
    comments: a string containing the comments.
    fullname: a string containing the full name.
    key_path: a string containing the Windows Registry key path.
    login_count: an integer containing the login count.
    offset: an integer containing the data offset of the SAM users
            Windows Registry value.
    username: a string containing the username.
  """
  DATA_TYPE = u'windows:registry:sam_users'

  def __init__(
      self, filetime, timestamp_description, key_path, offset, account_rid,
      login_count, username, fullname, comments):
    """Initializes a SAM users Windows Registry event.

    Args:
      filetime: an integer containing a FILETIME timestamp.
      timestamp_description: a string containing the usage of
                             the timestamp value.
      key_path: a string containing the Windows Registry key path.
      offset: an integer containing the data offset of the SAM users
              Windows Registry value.
      account_rid: an integer containing the account relative identifier (RID).
      login_count: an integer containing the login count.
      username: a string containing the username.
      fullname: a string containing the full name.
      comments: a string containing the comments.
    """
    super(SAMUsersWindowsRegistryEvent, self).__init__(
        filetime, timestamp_description)
    self.account_rid = account_rid
    self.comments = comments
    self.fullname = fullname
    self.key_path = key_path
    self.login_count = login_count
    self.offset = offset
    self.username = username


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

  def GetEntries(self, parser_mediator, registry_key, **kwargs):
    """Collect data from Users and Names and produce event objects.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
    """
    names_key = registry_key.GetSubkeyByName(u'Names')
    if not names_key:
      parser_mediator.ProduceExtractionError(u'missing subkey: "Names".')
      return

    values = [(v.name, v.last_written_time) for v in names_key.GetSubkeys()]

    usernames_dict = dict(values)

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

      filetime = None
      if usernames_dict:
        filetime = usernames_dict.get(username, None)

      # TODO: check if subkey.name == f_data_struct.rid

      if filetime:
        values_dict = {
            u'account_rid': f_data_struct.rid,
            u'login_count': f_data_struct.login_count}

        if username:
          values_dict[u'username'] = username
        if fullname:
          values_dict[u'full_name'] = fullname
        if comments:
          values_dict[u'comments'] = comments

        event_object = windows_events.WindowsRegistryEvent(
            filetime, registry_key.path, values_dict,
            offset=registry_key.offset, source_append=self._SOURCE_APPEND)
        parser_mediator.ProduceEvent(event_object)

      if f_data_struct.last_login > 0:
        event_object = SAMUsersWindowsRegistryEvent(
            f_data_struct.last_login, eventdata.EventTimestamp.LAST_LOGIN_TIME,
            registry_key.path, f_value.offset, f_data_struct.rid,
            f_data_struct.login_count, username, fullname, comments)
        parser_mediator.ProduceEvent(event_object)

      if f_data_struct.password_reset > 0:
        event_object = SAMUsersWindowsRegistryEvent(
            f_data_struct.password_reset,
            eventdata.EventTimestamp.LAST_PASSWORD_RESET,
            registry_key.path, f_value.offset, f_data_struct.rid,
            f_data_struct.login_count, username, fullname, comments)
        parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugin(SAMUsersWindowsRegistryPlugin)
