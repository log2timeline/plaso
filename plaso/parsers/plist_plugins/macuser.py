# -*- coding: utf-8 -*-
"""This file contains the Mac OS X user plist plugin."""

# TODO: Only plists from Mac OS X 10.8 and 10.9 were tested. Look at other
#       versions as well.

import binascii
import logging

from xml.etree import ElementTree

from binplist import binplist
from dfdatetime import time_elements as dfdatetime_time_elements
from dfvfs.file_io import fake_file_io
from dfvfs.path import fake_path_spec
from dfvfs.resolver import context

from plaso.containers import plist_event
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


class MacUserPlugin(interface.PlistPlugin):
  """Basic plugin to extract timestamp Mac user information.

  Further details about the extracted fields.
    name:
      string with the system user.
    uid:
      user ID.
    passwordpolicyoptions:
      XML Plist structures with the timestamp.
    passwordLastSetTime:
      last time the password was changed.
    lastLoginTimestamp:
      last time the user was authenticated depending on the situation,
      these timestamps are reset (0 value). It is translated by the
      library as a 2001-01-01 00:00:00 (COCAO zero time representation).
      If this happens, the event is not yield.
    failedLoginTimestamp:
      last time the user passwd was incorrectly(*).
    failedLoginCount:
      times of incorrect passwords.
  """

  NAME = u'macuser'
  DESCRIPTION = u'Parser for Mac OS X user plist files.'

  # The PLIST_PATH is dynamic, "user".plist is the name of the
  # Mac OS X user.
  PLIST_KEYS = frozenset([
      u'name', u'uid', u'home', u'passwordpolicyoptions', u'ShadowHashData'])

  _ROOT = u'/'

  def Process(self, parser_mediator, plist_name, top_level, **kwargs):
    """Check if it is a valid Mac OS X system  account plist file name.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      plist_name (str): name of the plist.
      top_level (dict[str, object]): plist top-level key.
    """
    super(MacUserPlugin, self).Process(
        parser_mediator, plist_name=self.PLIST_PATH, top_level=top_level)

  def GetEntries(self, parser_mediator, match=None, **unused_kwargs):
    """Extracts relevant user timestamp entries.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
    """
    if u'name' not in match or u'uid' not in match:
      return

    account = match[u'name'][0]
    uid = match[u'uid'][0]

    # INFO: binplist return a string with the Plist XML.
    for policy in match.get(u'passwordpolicyoptions', []):
      try:
        xml_policy = ElementTree.fromstring(policy)
      except (ElementTree.ParseError, LookupError) as exception:
        logging.error((
            u'Unable to parse XML structure for an user policy, account: '
            u'{0:s} and uid: {1!s}, with error: {2:s}').format(
                account, uid, exception))
        continue

      for dict_elements in xml_policy.iterfind(u'dict'):
        key_values = [value.text for value in dict_elements.getchildren()]
        # Taking a list and converting it to a dict, using every other item
        # as the key and the other one as the value.
        policy_dict = dict(zip(key_values[0::2], key_values[1::2]))

      time_string = policy_dict.get(u'passwordLastSetTime', None)
      if time_string and time_string != u'2001-01-01T00:00:00Z':
        try:
          date_time = dfdatetime_time_elements.TimeElements()
          date_time.CopyFromStringISO8601(time_string)
        except ValueError:
          date_time = None
          parser_mediator.ProduceExtractionError(
              u'unable to parse passworkd last set time string: {0:s}'.format(
                  time_string))

        shadow_hash_data = match.get(u'ShadowHashData', None)
        if date_time and isinstance(shadow_hash_data, (list, tuple)):
          # Extract the hash password information.
          # It is store in the attribute ShadowHasData which is
          # a binary plist data; However binplist only extract one
          # level of binary plist, then it returns this information
          # as a string.

          # TODO: change this into a DataRange instead. For this we
          # need the file offset and size of the ShadowHashData value data.
          shadow_hash_data = shadow_hash_data[0]

          resolver_context = context.Context()
          fake_file = fake_file_io.FakeFile(
              resolver_context, shadow_hash_data)
          shadow_hash_data_path_spec = fake_path_spec.FakePathSpec(
              location=u'ShadowHashData')
          fake_file.open(path_spec=shadow_hash_data_path_spec)

          try:
            plist_file = binplist.BinaryPlist(file_obj=fake_file)
            top_level = plist_file.Parse()
          except binplist.FormatError:
            top_level = dict()
          salted_hash = top_level.get(u'SALTED-SHA512-PBKDF2', None)
          if salted_hash:
            password_hash = u'$ml${0:d}${1:s}${2:s}'.format(
                salted_hash[u'iterations'],
                binascii.hexlify(salted_hash[u'salt']),
                binascii.hexlify(salted_hash[u'entropy']))
          else:
            password_hash = u'N/A'

          event_data = plist_event.PlistTimeEventData()
          event_data.desc = (
              u'Last time {0:s} ({1!s}) changed the password: {2!s}').format(
                  account, uid, password_hash)
          event_data.key = u'passwordLastSetTime'
          event_data.root = self._ROOT

          event = time_events.DateTimeValuesEvent(
              date_time, definitions.TIME_DESCRIPTION_WRITTEN)
          parser_mediator.ProduceEventWithEventData(event, event_data)

      time_string = policy_dict.get(u'lastLoginTimestamp', None)
      if time_string and time_string != u'2001-01-01T00:00:00Z':
        try:
          date_time = dfdatetime_time_elements.TimeElements()
          date_time.CopyFromStringISO8601(time_string)
        except ValueError:
          date_time = None
          parser_mediator.ProduceExtractionError(
              u'unable to parse last login time string: {0:s}'.format(
                  time_string))

        if date_time:
          event_data = plist_event.PlistTimeEventData()
          event_data.desc = u'Last login from {0:s} ({1!s})'.format(
              account, uid)
          event_data.key = u'lastLoginTimestamp'
          event_data.root = self._ROOT

          event = time_events.DateTimeValuesEvent(
              date_time, definitions.TIME_DESCRIPTION_WRITTEN)
          parser_mediator.ProduceEventWithEventData(event, event_data)

      time_string = policy_dict.get(u'failedLoginTimestamp', None)
      if time_string and time_string != u'2001-01-01T00:00:00Z':
        try:
          date_time = dfdatetime_time_elements.TimeElements()
          date_time.CopyFromStringISO8601(time_string)
        except ValueError:
          date_time = None
          parser_mediator.ProduceExtractionError(
              u'unable to parse failed login time string: {0:s}'.format(
                  time_string))

        if date_time:
          event_data = plist_event.PlistTimeEventData()
          event_data.desc = (
              u'Last failed login from {0:s} ({1!s}) ({2!s} times)').format(
                  account, uid, policy_dict.get(u'failedLoginCount', 0))
          event_data.key = u'failedLoginTimestamp'
          event_data.root = self._ROOT

          event = time_events.DateTimeValuesEvent(
              date_time, definitions.TIME_DESCRIPTION_WRITTEN)
          parser_mediator.ProduceEventWithEventData(event, event_data)


plist.PlistParser.RegisterPlugin(MacUserPlugin)
