# -*- coding: utf-8 -*-
""""Windows Registry plugin for SAM Users Account information."""

import logging

import construct

from plaso.containers import windows_events
from plaso.lib import binary
from plaso.lib import eventdata
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


__author__ = 'Preston Miller, dpmforensics.com, github.com/prmiller91'


class SAMUsersWindowsRegistryEvent(time_events.FiletimeEvent):
  """Convenience class for a SAM users Windows Registry event.

  Attributes:
    key_path: a string containing the Windows Registry key path.
    offset: an integer containing the data offset of the SAM users
            Windows Registry value.
    regvalue: a dictionary containing the UserAssist values.
  """

  DATA_TYPE = 'windows:registry:sam_users'

  def __init__(
      self, filetime, timestamp_description, key_path, offset, values_dict):
    """Initializes a SAM users Windows Registry event.

    Args:
      filetime: an integer containing a FILETIME timestamp.
      timestamp_description: a string containing the usage of
                             the timestamp value.
      key_path: a string containing the Windows Registry key path.
      offset: an integer containing the data offset of the SAM users
              Windows Registry value.
      values_dict: dictionary object containing the UserAssist values.
    """
    super(SAMUsersWindowsRegistryEvent, self).__init__(
        filetime, timestamp_description)
    self.key_path = key_path
    self.offset = offset
    # TODO: rename regvalue to ???.
    self.regvalue = values_dict


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

  _V_VALUE_HEADER_SIZE = _V_VALUE_HEADER.sizeof()

  # TODO: refactor.
  def _ParseVValue(self, key):
    """Parses V value and returns name, fullname, and comments data.

    Args:
      key: Registry key (instance of dfwinreg.WinRegistryKey).

    Returns:
      name: Name data parsed with name start and length values.
      fullname: Fullname data parsed with fullname start and length values.
      comments: Comments data parsed with comments start and length values.
    """
    name_offset = structure.values()[0][3] + self._V_VALUE_HEADER_SIZE
    full_name_offset = structure.values()[0][6] + self._V_VALUE_HEADER_SIZE
    comments_offset = structure.values()[0][9] + self._V_VALUE_HEADER_SIZE
    name_raw = v_value.data[
        name_offset:name_offset + structure.values()[0][4]]
    full_name_raw = v_value.data[
        full_name_offset:full_name_offset + structure.values()[0][7]]
    comments_raw = v_value.data[
        comments_offset:comments_offset + structure.values()[0][10]]
    name = binary.ReadUTF16(name_raw)
    full_name = binary.ReadUTF16(full_name_raw)
    comments = binary.ReadUTF16(comments_raw)
    return name, full_name, comments

  def GetEntries(self, parser_mediator, registry_key, **kwargs):
    """Collect data from Users and Names and produce event objects.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
    """
    names_key = registry_key.GetSubkeyByName(u'Names')
    if not names_key:
      parser_mediator.ProduceParseError(u'missing subkey: "Names".')
      return

    values = [(v.name, v.last_written_time) for v in names_key.GetSubkeys()]

    name_dict = dict(values)

    for subkey in registry_key.GetSubkeys():
      if subkey.name == u'Names':
        continue

      f_value = subkey.GetValueByName(u'F')
      if not f_value:
        parser_mediator.ProduceParseError(
            u'missing Registry value: "F" in subkey: {0:s}.'.format(
                subkey.name))
        continue

      v_value = key.GetValueByName(u'V')
      if not v_value:
        parser_mediator.ProduceParseError(
            u'missing Registry value: "V" in subkey: {0:s}.'.format(
                subkey.name))
        continue

      try:
        f_data_struct = self._F_VALUE_STRUCT.parse(f_value.data)
      except construct.FieldError as exception:
        parser_mediator.ProduceParseError((
            u'unable to parse Registry value: "F" in subkey: {0:s} '
            u'with error: {1:s}.').format(subkey.name, exception))
        continue

      try:
        v_data_struct = self._V_VALUE_STRUCT.parse(v_value.data)
      except construct.FieldError as exception:
        parser_mediator.ProduceParseError((
            u'unable to parse Registry value: "V" in subkey: {0:s} '
            u'with error: {1:s}.').format(subkey.name, exception))
        continue

      username_offset = v_data_struct.values()[0][3] + self._V_VALUE_HEADER_SIZE
      fullname_offset = v_data_struct.values()[0][6] + self._V_VALUE_HEADER_SIZE
      comments_offset = v_data_struct.values()[0][9] + self._V_VALUE_HEADER_SIZE
      username_raw = v_value.data[
          username_offset:username_offset + v_data_struct.values()[0][4]]
      fullname_raw = v_value.data[
          fullname_offset:fullname_offset + v_data_struct.values()[0][7]]
      comments_raw = v_value.data[
          comments_offset:comments_offset + v_data_struct.values()[0][10]]

      username = binary.ReadUTF16(username_raw)
      fullname = binary.ReadUTF16(fullname_raw)
      comments = binary.ReadUTF16(comments_raw)

      values_dict = {u'user_guid': subkey.name}

      if username:
        values_dict[u'username'] = username
      if fullname:
        values_dict[u'full_name'] = fullname
      if comments:
        values_dict[u'comments'] = comments
      if name_dict:
        account_create_time = name_dict.get(username, 0)
      else:
        account_create_time = 0

      values_dict[u'account_rid'] = f_data_struct.rid
      values_dict[u'login_count'] = f_data_struct.login_count

      if account_create_time > 0:
        event_object = SAMUsersWindowsRegistryEvent(
            account_create_time, eventdata.EventTimestamp.ACCOUNT_CREATED,
            registry_key.path, values_dict,
            offset=registry_key.offset)
        parser_mediator.ProduceEvent(event_object)

      if f_data_struct.last_login > 0:
        event_object = SAMUsersWindowsRegistryEvent(
            f_data_struct.last_login, eventdata.EventTimestamp.LAST_LOGIN_TIME,
            registry_key.path, f_value.offset, values_dict)
        parser_mediator.ProduceEvent(event_object)

      if f_data_struct.password_reset > 0:
        event_object = SAMUsersWindowsRegistryEvent(
            f_data_struct.password_reset,
            eventdata.EventTimestamp.LAST_PASSWORD_RESET,
            registry_key.path, f_value.offset, values_dict)
        parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugin(SAMUsersWindowsRegistryPlugin)
