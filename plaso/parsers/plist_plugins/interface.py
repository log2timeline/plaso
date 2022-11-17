# -*- coding: utf-8 -*-
"""Interface for plist parser plugins.

Plist files are only one example of a type of object that the Plaso tool is
expected to encounter and process. There can be and are many other parsers
which are designed to process specific data types.

PlistPlugin defines the attributes necessary for registration, discovery
and operation of plugins for plist files which will be used by PlistParser.
"""

import abc

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.parsers import logger
from plaso.parsers import plugins


class PlistPathFilter(object):
  """The plist path filter."""

  def __init__(self, filename):
    """Initializes a plist path filter.

    Args:
      filename (str): expected file name of the plist.
    """
    super(PlistPathFilter, self).__init__()
    self._filename_lower_case = filename.lower()

  def Match(self, filename_lower_case):
    """Determines if a plist filename matches the filter.

    Note that this method does a case insensitive comparison.

    Args:
      filename_lower_case (str): filename of the plist in lower case.

    Returns:
      bool: True if the filename matches the filter.
    """
    return bool(filename_lower_case == self._filename_lower_case)


class PrefixPlistPathFilter(PlistPathFilter):
  """The prefix plist path filter."""

  def Match(self, filename_lower_case):
    """Determines if a plist filename matches the filter.

    Note that this method does a case insensitive comparison.

    Args:
      filename_lower_case (str): filename of the plist in lower case.

    Returns:
      bool: True if the filename matches the filter.
    """
    return filename_lower_case.startswith(self._filename_lower_case)


class PlistPlugin(plugins.BasePlugin):
  """This is an abstract class from which plugins should be based.

  The following are the attributes and methods expected to be overridden by a
  plugin.

  Attributes:
    PLIST_PATH_FILTERS (set[PlistPathFilter]): plist path filters that should
         match for the plugin to process the plist.
    PLIST_KEY (set[str]): keys holding values that are necessary for processing.

  Please note, PLIST_KEY is case sensitive and for a plugin to match a
  plist file needs to contain at minimum the number of keys needed for
  processing.

  For example if a Plist file contains the following keys,
  {'foo': 1, 'bar': 2, 'opt': 3} with 'foo' and 'bar' being keys critical to
  processing define PLIST_KEY as ['foo', 'bar']. If 'opt' is only optionally
  defined it can still be accessed by manually processing self.top_level from
  the plugin.
  """

  NAME = 'plist_plugin'

  # This is expected to be overridden by the processing plugin, for example:
  # frozenset(PlistPathFilter('com.apple.bluetooth.plist'))
  PLIST_PATH_FILTERS = frozenset()

  # PLIST_KEYS is a list of keys required by a plugin.
  # This is expected to be overridden by the processing plugin.
  # Ex. frozenset(['DeviceCache', 'PairedDevices'])
  PLIST_KEYS = frozenset(['any'])

  def _GetDateTimeValueFromPlistKey(self, plist_key, plist_value_name):
    """Retrieves a date and time value from a specific value in a plist key.

    Args:
      plist_key (object): plist key.
      plist_value_name (str): name of the value in the plist key.

    Returns:
      dfdatetime.TimeElementsInMicroseconds: date and time or None if not
          available.
    """
    datetime_value = plist_key.get(plist_value_name, None)
    if not datetime_value:
      return None

    date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
    date_time.CopyFromDatetime(datetime_value)
    return date_time

  def _GetKeys(self, top_level, keys, depth=1):
    """Helper function to return keys nested in a plist dict.

    By default this function will return the values for the named keys requested
    by a plugin in match dictionary object. The default setting is to look
    a single level down from the root, which is suitable for most cases.

    For cases where there is variability in the name at the first level, for
    example the name is the MAC address of a device or a UUID, it is possible
    to override the depth limit and use GetKeys to fetch from a deeper level.

    E.g.
    Top_Level (root):                                             # depth = 0
    -- Key_Name_is_UUID_Generated_At_Install 1234-5678-8          # depth = 1
    ---- Interesting_SubKey_with_value_to_Process: [Values, ...]  # depth = 2

    Args:
      top_level (dict[str, object]): plist top-level key.
      keys (list[str]): names of the keys that should be returned.
      depth (int): number of levels to check for a match.

    Returns:
      dict[str, object]: the keys requested or an empty set if the plist is
          flat, for example the top level is a list instead of a dictionary.
    """
    match = {}
    if not isinstance(top_level, dict):
      # Return an empty dict here if top_level is a list object, which happens
      # if the plist file is flat.
      return match
    keys = set(keys)

    if depth == 1:
      for key in keys:
        match[key] = top_level.get(key, None)

    else:
      for _, parsed_key, parsed_value in self._RecurseKey(
          top_level, depth=depth):
        if parsed_key in keys:
          match[parsed_key] = parsed_value
          if set(match.keys()) == keys:
            return match

    return match

  def _RecurseKey(self, plist_item, depth=15, key_path=''):
    """Flattens nested dictionaries and lists by yielding its values.

    The hierarchy of a plist file is a series of nested dictionaries and lists.
    This is a helper function helps plugins navigate the structure without
    having to reimplement their own recursive methods.

    This method implements an overridable depth limit to prevent processing
    extremely deeply nested plists. If the limit is reached a debug message is
    logged indicating which key processing stopped on.

    Example Input Plist:
      plist_item = { DeviceRoot: { DeviceMAC1: [Value1, Value2, Value3],
                                   DeviceMAC2: [Value1, Value2, Value3]}}

    Example Output:
      ('', DeviceRoot, {DeviceMACs...})
      (DeviceRoot, DeviceMAC1, [Value1, Value2, Value3])
      (DeviceRoot, DeviceMAC2, [Value1, Value2, Value3])

    Args:
      plist_item (object): plist item to be checked for additional nested items.
      depth (Optional[int]): current recursion depth. This value is used to
          ensure we stop at the maximum recursion depth.
      key_path (Optional[str]): path of the current working key.

    Yields:
      tuple[str, str, object]: key path, key name and value.
    """
    if depth < 1:
      logger.debug(
          'Maximum recursion depth of 15 reached for key: {0:s}'.format(
              key_path))

    elif isinstance(plist_item, (list, tuple)):
      for sub_plist_item in plist_item:
        for subkey_values in self._RecurseKey(
            sub_plist_item, depth=depth - 1, key_path=key_path):
          yield subkey_values

    elif hasattr(plist_item, 'items'):
      for subkey_name, value in plist_item.items():
        yield key_path, subkey_name, value

        if isinstance(value, dict):
          value = [value]
        elif not isinstance(value, (list, tuple)):
          continue

        for sub_plist_item in value:
          if isinstance(sub_plist_item, dict):
            subkey_path = '{0:s}/{1:s}'.format(key_path, subkey_name)
            for subkey_values in self._RecurseKey(
                sub_plist_item, depth=depth - 1, key_path=subkey_path):
              yield subkey_values

  # pylint: disable=arguments-differ
  @abc.abstractmethod
  def _ParsePlist(
      self, parser_mediator, match=None, top_level=None, **unused_kwargs):
    """Extracts events from the values of entries within a plist.

    This is the main method that a plist plugin needs to implement.

    The contents of the plist keys defined in PLIST_KEYS will be made available
    to the plugin as self.matched{'KEY': 'value'}. The plugin should implement
    logic to parse this into a useful event for incorporation into the Plaso
    timeline.

    For example if you want to note the timestamps of when devices were
    LastInquiryUpdated you would need to examine the bluetooth config file
    called 'com.apple.bluetooth' and need to look at devices under the key
    'DeviceCache'. To do this the plugin needs to define:
        PLIST_PATH_FILTERS = frozenset([
            interface.PlistPathFilter('com.apple.bluetooth')])
        PLIST_KEYS = frozenset(['DeviceCache']).

    When a file with this key is encountered during processing self.matched is
    populated and the plugin's _ParsePlist() is called. The plugin would have
    self.matched = {'DeviceCache': [{'DE:AD:BE:EF:01': {'LastInquiryUpdate':
    DateTime_Object}, 'DE:AD:BE:EF:01': {'LastInquiryUpdate':
    DateTime_Object}'...}]} and needs to implement logic here to extract
    values, format, and produce the data as an event.PlistEvent.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
      top_level (Optional[dict[str, object]]): plist top-level item.
    """

  def Process(self, parser_mediator, top_level=None, **kwargs):
    """Extracts events from a plist file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      top_level (Optional[dict[str, object]]): plist top-level item.
    """
    # This will raise if unhandled keyword arguments are passed.
    super(PlistPlugin, self).Process(parser_mediator)

    match = self._GetKeys(top_level, self.PLIST_KEYS)
    self._ParsePlist(parser_mediator, match=match, top_level=top_level)
