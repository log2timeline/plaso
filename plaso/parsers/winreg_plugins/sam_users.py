# -*- coding: utf-8 -*-

import construct
import logging
from plaso.events import windows_events
from plaso.lib import binary
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


__author__ = 'Preston Miller, dpmforensics.com, github.com/prmiller91'


class UsersPlugin(interface.WindowsRegistryPlugin):
  """SAM Windows Registry plugin for Users Account information."""

  NAME = u'windows_sam_users'
  DESCRIPTION = u'Parser for SAM Users and Names Registry keys.'

  REG_KEYS = [u'\\SAM\\Domains\\Account\\Users']
  REG_TYPE = u'SAM'

  F_VALUE_STRUCT = construct.Struct(
      u'f_struct',
      construct.Padding(8),
      construct.ULInt64(u'last_login'),
      construct.Padding(8),
      construct.ULInt64(u'password_reset'),
      construct.Padding(16),
      construct.ULInt16(u'rid'),
      construct.Padding(16),
      construct.ULInt8(u'login_count'))
  V_VALUE_HEADER = construct.Struct(
      u'v_header',
      construct.Array(11, construct.ULInt32(u'values')))
  V_VALUE_HEADER_SIZE = 0xCC

  def GetEntries(
      self, parser_mediator, key=None, registry_type=None, codepage=u'cp1252',
      **unused_kwargs):
    """Collect data from Users and Names and produce event objects.

    Args:
      parser_mediator: A parser context object (instance of ParserContext).
      key: Optional Registry key (instance of winreg.WinRegKey).
           The default is None.
      registry_type: Optional Registry type string. The default is None.
    """

    name_dict = {}

    name_key = key.GetSubkey(u'Names')
    if not name_key:
      parser_mediator.ProduceParseError(u'Unable to locate Names key.')
      return
    values = [(v.name, v.last_written_timestamp) for v in name_key.GetSubkeys()]
    name_dict = dict(values)

    for subkey in key.GetSubkeys():
      text_dict = {}
      if subkey.name == u'Names':
        continue
      text_dict[u'user_guid'] = subkey.name
      parsed_v_value = self._ParseVValue(subkey)
      if not parsed_v_value:
        parser_mediator.ProduceParseError(
            u'Unable to parse SAM key: {0:s} V value.'.format(subkey))
        return
      username = parsed_v_value[0]
      full_name = parsed_v_value[1]
      comments = parsed_v_value[2]
      if username:
        text_dict[u'username'] = username
      if full_name:
        text_dict[u'full_name'] = full_name
      if comments:
        text_dict[u'comments'] = comments
      if name_dict:
        account_create_time = name_dict.get(text_dict.get(u'username'), 0)
      else:
        account_create_time = 0

      f_data = self._ParseFValue(subkey)
      last_login_time = timelib.Timestamp.FromFiletime(f_data.last_login)
      password_reset_time = timelib.Timestamp.FromFiletime(
          f_data.password_reset)
      text_dict[u'account_rid'] = f_data.rid
      text_dict[u'login_count'] = f_data.login_count

      if account_create_time > 0:
        event_object = windows_events.WindowsRegistryEvent(
            account_create_time, key.path, text_dict,
            usage=eventdata.EventTimestamp.ACCOUNT_CREATED,
            offset=key.offset, registry_type=registry_type,
            source_append=u'User Account Information')
        parser_mediator.ProduceEvent(event_object)

      if last_login_time > 0:
        event_object = windows_events.WindowsRegistryEvent(
            last_login_time, key.path, text_dict,
            usage=eventdata.EventTimestamp.LAST_LOGIN_TIME,
            offset=key.offset,
            registry_type=registry_type,
            source_append=u'User Account Information')
        parser_mediator.ProduceEvent(event_object)

      if password_reset_time > 0:
        event_object = windows_events.WindowsRegistryEvent(
            password_reset_time, key.path, text_dict,
            usage=eventdata.EventTimestamp.LAST_PASSWORD_RESET,
            offset=key.offset, registry_type=registry_type,
            source_append=u'User Account Information')
        parser_mediator.ProduceEvent(event_object)

  def _ParseVValue(self, key):
    """Parses V value and returns name, fullname, and comments data.

    Args:
      key: Registry key (instance of winreg.WinRegKey).

    Returns:
      name: Name data parsed with name start and length values.
      fullname: Fullname data parsed with fullname start and length values.
      comments: Comments data parsed with comments start and length values.
    """

    v_value = key.GetValue(u'V')
    if not v_value:
      logging.error(u'Unable to locate V Value in key.')
      return
    try:
      structure = self.V_VALUE_HEADER.parse(v_value.data)
    except construct.FieldError as exception:
      logging.error(
          u'Unable to extract V value header data: {:s}'.format(exception))
      return
    name_offset = structure.values()[0][3] + self.V_VALUE_HEADER_SIZE
    full_name_offset = structure.values()[0][6] + self.V_VALUE_HEADER_SIZE
    comments_offset = structure.values()[0][9] + self.V_VALUE_HEADER_SIZE
    name_raw = v_value.data[
        name_offset:name_offset + structure.values()[0][4]]
    full_name_raw = v_value.data[
        full_name_offset:full_name_offset + structure.values()[0][7]]
    comments_raw = v_value.data[
        comments_offset:comments_offset + structure.values()[0][10]]
    name = binary.ReadUtf16(name_raw)
    full_name = binary.ReadUtf16(full_name_raw)
    comments = binary.ReadUtf16(comments_raw)
    return name, full_name, comments

  def _ParseFValue(self, key):
    """Parses F value and returns parsed F data construct object.

    Args:
      key: Registry key (instance of winreg.WinRegKey).

    Returns:
      f_data: Construct parsed F value containing rid, login count,
              and timestamp information.
    """
    f_value = key.GetValue(u'F')
    if not f_value:
      logging.error(u'Unable to locate F Value in key.')
      return
    try:
      f_data = self.F_VALUE_STRUCT.parse(f_value.data)
    except construct.FieldError as exception:
      logging.error(
          u'Unable to extract F value data: {:s}'.format(exception))
      return
    return f_data


winreg.WinRegistryParser.RegisterPlugin(UsersPlugin)
