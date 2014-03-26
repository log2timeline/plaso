#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This file contains a default plist plugin in Plaso."""

# TODO: Only plists from Mac OS X 10.8 and 10.9 were tested. Look at other
#       versions as well.

import binascii
from xml.etree import ElementTree

from plaso.events import plist_event
from plaso.lib import timelib
from plaso.parsers.plist_plugins import interface

from binplist import binplist

__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


class MacUserPlugin(interface.PlistPlugin):
  """Basic plugin to extract timestamp Mac user information."""

  NAME = 'plist_macuser'

  # The PLIST_PATH is dynamic, "user".plist is the name of the
  # Mac OS X user.
  PLIST_KEYS = frozenset(
      ['name', 'uid', 'home',
       'passwordpolicyoptions', 'ShadowHashData'])

  def Process(self, plist_name=None, top_level=None, **kwargs):
    """Check if it is a valid Mac OS X system  account plist file name.

    Args:
      plist_name: name of the plist file.
      top_level: dictionary with the plist file parsed.

    Returns:
      A MacUserPlugin event with a valid plist name.
    """
    return super(MacUserPlugin, self).Process(
        plist_name=self.PLIST_PATH, top_level=top_level, **kwargs)

  # Yield Events
  # name: string with the system user.
  # uid: user ID.
  # passwordpolicyoptions: XML Plist structures with the timestamp.
  #   passwordLastSetTime: last time the password was changed.
  #   lastLoginTimestamp: last time the user was authenticated (*).
  #   failedLoginTimestamp: last time the user passwd was incorrectly(*).
  #   failedLoginCount: times of incorrect passwords.
  #   (*): depending on the situation, these timestamps are reset (0 value).
  #        It is translated by the library as a 2001-01-01 00:00:00 (COCAO
  #        zero time representation). If this happens, the event is not yield.

  def GetEntries(self, match, **unused_kwargs):
    """Extracts relevant user timestamp entries.

    Args:
      match: A dictionary containing keys extracted from PLIST_KEYS.

    Yields:
      EventObject objects extracted from the plist.
    """
    root = '/'
    account = match['name'][0]
    uid = match['uid'][0]
    cocoa_zero = (
        timelib.Timestamp.COCOA_TIME_TO_POSIX_BASE *
        timelib.Timestamp.MICRO_SECONDS_PER_SECOND)
    # INFO: binplist return a string with the Plist XML.
    for policy in match['passwordpolicyoptions']:
      xml_policy = ElementTree.fromstring(policy)
      for dict_elements in xml_policy.iterfind('dict'):
        key_values = [value.text for value in dict_elements.getchildren()]
        policy_dict = dict(zip(key_values[0::2], key_values[1::2]))

      if policy_dict.get('passwordLastSetTime', 0):
        timestamp = timelib.Timestamp.FromTimeString(
             policy_dict.get('passwordLastSetTime', '0'))
        if timestamp > cocoa_zero:
          # Extract the hash password information.
          # It is store in the attribure ShadowHasData which is
          # a binary plist data; However binplist only extract one
          # level of binary plist, then it returns this information
          # as a string.
          fake_file = interface.FakeFile(match['ShadowHashData'][0])
          try:
            plist_file = binplist.BinaryPlist(file_obj=fake_file)
            top_level = plist_file.Parse()
          except binplist.FormatError:
            top_level = dict()
          salted_hash = top_level.get('SALTED-SHA512-PBKDF2', None)
          if salted_hash:
            password_hash = u'$ml${}${}${}'.format(
                salted_hash['iterations'],
                binascii.hexlify(salted_hash['salt']),
                binascii.hexlify(salted_hash['entropy']))
          else:
            password_hash = u'N/A'
          description = u'Last time {} ({}) changed the password: {}'.format(
              account, uid, password_hash)
          yield plist_event.PlistEvent(
              root, u'passwordLastSetTime', timestamp, description)

      if policy_dict.get('lastLoginTimestamp', 0):
        timestamp = timelib.Timestamp.FromTimeString(
             policy_dict.get('lastLoginTimestamp', '0'))
        description = u'Last login from {} ({})'.format(
            account, uid)
        if timestamp > cocoa_zero:
          yield plist_event.PlistEvent(
              root, u'lastLoginTimestamp', timestamp, description)

      if policy_dict.get('failedLoginTimestamp', 0):
        timestamp = timelib.Timestamp.FromTimeString(
             policy_dict.get('failedLoginTimestamp', '0'))
        description = u'Last failed login from {} ({}) ({} times)'.format(
            account, uid, policy_dict['failedLoginCount'])
        if timestamp > cocoa_zero:
          yield plist_event.PlistEvent(
              root, u'failedLoginTimestamp', timestamp, description)

