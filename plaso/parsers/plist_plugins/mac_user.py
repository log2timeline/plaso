# -*- coding: utf-8 -*-
"""Plist parser plugin for MacOS user plist files."""

# TODO: Only plists from MacOS 10.8 and 10.9 were tested. Look at other
#       versions as well.

import codecs
import plistlib

from xml.parsers import expat

from defusedxml import ElementTree
from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import logger
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class MacOSUserEventData(events.EventData):
  """MacOS user event data.

  Attributes:
    fullname (str): full name.
    home_directory (str): path of the home directory.
    number_of_failed_login_attempts (str): number of failed login attempts.
    password_hash (str): password hash.
    user_identifier (str): user identifier.
    username (str): username.
  """

  DATA_TYPE = 'macos:user:entry'

  def __init__(self):
    """Initializes event data."""
    super(MacOSUserEventData, self).__init__(data_type=self.DATA_TYPE)
    self.fullname = None
    self.home_directory = None
    self.number_of_failed_login_attempts = None
    self.password_hash = None
    self.user_identifier = None
    self.username = None


class MacOSUserPlistPlugin(interface.PlistPlugin):
  """Plist parser plugin for MacOS user plist files.

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
      library as a 2001-01-01 00:00:00 (Cocoa zero time representation).
      If this happens, the event is not yield.
    failedLoginTimestamp:
      last time the user passwd was incorrectly(*).
    failedLoginCount:
      times of incorrect passwords.
  """

  NAME = 'macuser'
  DATA_FORMAT = 'MacOS user plist file'

  # The PLIST_PATH is dynamic, "user".plist is the name of the
  # MacOS user.
  PLIST_KEYS = frozenset([
      'name', 'uid', 'home', 'passwordpolicyoptions', 'ShadowHashData'])

  _ROOT = '/'

  # pylint: disable=arguments-differ
  def _ParsePlist(
      self, parser_mediator, match=None, top_level=None, **unused_kwargs):
    """Extracts relevant user timestamp entries.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
      top_level (Optional[dict[str, object]]): plist top-level item.
    """
    if 'name' not in match or 'uid' not in match:
      return

    fullname = top_level.get('realname', [None])[0]
    home_directory = top_level.get('home', [None])[0]
    password_hash = None
    user_identifier = match['uid'][0]
    username = match['name'][0]

    shadow_hash_data = match.get('ShadowHashData', None)
    if isinstance(shadow_hash_data, (list, tuple)):
      # Extract the hash password information, which is stored in
      # the attribute ShadowHashData which is a binary plist data.
      try:
        property_list = plistlib.loads(shadow_hash_data[0])
      except plistlib.InvalidFileException as exception:
        parser_mediator.ProduceExtractionWarning(
            'unable to parse ShadowHashData with error: {0!s}'.format(
                exception))
        property_list = {}

      salted_hash = property_list.get('SALTED-SHA512-PBKDF2', None)
      if salted_hash:
        salt_hex_bytes = codecs.encode(salted_hash['salt'], 'hex')
        salt_string = codecs.decode(salt_hex_bytes, 'ascii')
        entropy_hex_bytes = codecs.encode(salted_hash['entropy'], 'hex')
        entropy_string = codecs.decode(entropy_hex_bytes, 'ascii')
        password_hash = '$ml${0:d}${1:s}${2:s}'.format(
            salted_hash['iterations'], salt_string, entropy_string)

    for policy in match.get('passwordpolicyoptions', []):
      try:
        xml_policy = ElementTree.fromstring(policy)
      except (LookupError, ElementTree.ParseError,
              expat.ExpatError) as exception:
        logger.error((
            'Unable to parse XML structure for an user policy, username: '
            '{0:s} and UID: {1!s}, with error: {2!s}').format(
                username, user_identifier, exception))
        continue

      for dict_elements in xml_policy.iterfind('dict'):
        key_values = [value.text for value in dict_elements]
        # Taking a list and converting it to a dict, using every other item
        # as the key and the other one as the value.
        policy_dict = dict(zip(key_values[0::2], key_values[1::2]))

      time_string = policy_dict.get('passwordLastSetTime', None)
      if time_string and time_string != '2001-01-01T00:00:00Z':
        try:
          date_time = dfdatetime_time_elements.TimeElements()
          date_time.CopyFromStringISO8601(time_string)
        except ValueError:
          date_time = None
          parser_mediator.ProduceExtractionWarning(
              'unable to parse password last set time string: {0:s}'.format(
                  time_string))

        if date_time:
          event_data = MacOSUserEventData()
          event_data.fullname = fullname
          event_data.home_directory = home_directory
          event_data.password_hash = password_hash
          event_data.user_identifier = user_identifier
          event_data.username = username

          event = time_events.DateTimeValuesEvent(
              date_time, definitions.TIME_DESCRIPTION_LAST_PASSWORD_SET)
          parser_mediator.ProduceEventWithEventData(event, event_data)

      time_string = policy_dict.get('lastLoginTimestamp', None)
      if time_string and time_string != '2001-01-01T00:00:00Z':
        try:
          date_time = dfdatetime_time_elements.TimeElements()
          date_time.CopyFromStringISO8601(time_string)
        except ValueError:
          date_time = None
          parser_mediator.ProduceExtractionWarning(
              'unable to parse last login time string: {0:s}'.format(
                  time_string))

        if date_time:
          event_data = MacOSUserEventData()
          event_data.fullname = fullname
          event_data.home_directory = home_directory
          event_data.user_identifier = user_identifier
          event_data.username = username

          event = time_events.DateTimeValuesEvent(
              date_time, definitions.TIME_DESCRIPTION_LAST_LOGIN)
          parser_mediator.ProduceEventWithEventData(event, event_data)

      time_string = policy_dict.get('failedLoginTimestamp', None)
      if time_string and time_string != '2001-01-01T00:00:00Z':
        try:
          date_time = dfdatetime_time_elements.TimeElements()
          date_time.CopyFromStringISO8601(time_string)
        except ValueError:
          date_time = None
          parser_mediator.ProduceExtractionWarning(
              'unable to parse failed login time string: {0:s}'.format(
                  time_string))

        if date_time:
          event_data = MacOSUserEventData()
          event_data.fullname = fullname
          event_data.home_directory = home_directory
          event_data.number_of_failed_login_attempts = policy_dict.get(
              'failedLoginCount', None)
          event_data.user_identifier = user_identifier
          event_data.username = username

          event = time_events.DateTimeValuesEvent(
              date_time, definitions.TIME_DESCRIPTION_LAST_LOGIN_ATTEMPT)
          parser_mediator.ProduceEventWithEventData(event, event_data)


plist.PlistParser.RegisterPlugin(MacOSUserPlistPlugin)
