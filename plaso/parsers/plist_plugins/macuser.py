# -*- coding: utf-8 -*-
"""This file contains the Mac OS X user plist plugin."""

# TODO: Only plists from Mac OS X 10.8 and 10.9 were tested. Look at other
#       versions as well.

import binascii
import logging

from binplist import binplist
from dfvfs.file_io import fake_file_io
from dfvfs.path import fake_path_spec
from dfvfs.resolver import context
from xml.etree import ElementTree

from plaso.containers import plist_event
from plaso.lib import errors
from plaso.lib import timelib
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
      parser_mediator: A parser mediator object (instance of ParserMediator).
      plist_name: name of the plist file.
      top_level: dictionary with the plist file parsed.
    """
    super(MacUserPlugin, self).Process(
        parser_mediator, plist_name=self.PLIST_PATH, top_level=top_level)

  def GetEntries(self, parser_mediator, match=None, **unused_kwargs):
    """Extracts relevant user timestamp entries.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      match: Optional dictionary containing keys extracted from PLIST_KEYS.
    """
    if u'name' not in match or u'uid' not in match:
      return

    account = match[u'name'][0]
    uid = match[u'uid'][0]
    cocoa_zero = (
        timelib.Timestamp.COCOA_TIME_TO_POSIX_BASE *
        timelib.Timestamp.MICRO_SECONDS_PER_SECOND)

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
      if time_string:
        try:
          timestamp = timelib.Timestamp.FromTimeString(time_string)
        except errors.TimestampError:
          parser_mediator.ProduceParseError(
              u'Unable to parse time string: {0:s}'.format(time_string))
          timestamp = 0

        shadow_hash_data = match.get(u'ShadowHashData', None)
        if timestamp > cocoa_zero and isinstance(
            shadow_hash_data, (list, tuple)):
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
          fake_file.open(path_spec=fake_path_spec.FakePathSpec(
              location=u'ShadowHashData'))

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
          description = (
              u'Last time {0:s} ({1!s}) changed the password: {2!s}').format(
                  account, uid, password_hash)
          event_object = plist_event.PlistTimeEvent(
              self._ROOT, u'passwordLastSetTime', timestamp, description)
          parser_mediator.ProduceEvent(event_object)

      time_string = policy_dict.get(u'lastLoginTimestamp', None)
      if time_string:
        try:
          timestamp = timelib.Timestamp.FromTimeString(time_string)
        except errors.TimestampError:
          parser_mediator.ProduceParseError(
              u'Unable to parse time string: {0:s}'.format(time_string))
          timestamp = 0

        description = u'Last login from {0:s} ({1!s})'.format(account, uid)
        if timestamp > cocoa_zero:
          event_object = plist_event.PlistTimeEvent(
              self._ROOT, u'lastLoginTimestamp', timestamp, description)
          parser_mediator.ProduceEvent(event_object)

      time_string = policy_dict.get(u'failedLoginTimestamp', None)
      if time_string:
        try:
          timestamp = timelib.Timestamp.FromTimeString(time_string)
        except errors.TimestampError:
          parser_mediator.ProduceParseError(
              u'Unable to parse time string: {0:s}'.format(time_string))
          timestamp = 0

        description = (
            u'Last failed login from {0:s} ({1!s}) ({2!s} times)').format(
                account, uid, policy_dict.get(u'failedLoginCount', 0))
        if timestamp > cocoa_zero:
          event_object = plist_event.PlistTimeEvent(
              self._ROOT, u'failedLoginTimestamp', timestamp, description)
          parser_mediator.ProduceEvent(event_object)


plist.PlistParser.RegisterPlugin(MacUserPlugin)
