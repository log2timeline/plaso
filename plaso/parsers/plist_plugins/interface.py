# -*- coding: utf-8 -*-
"""Plist_interface contains basic interface for plist plugins within Plaso.

Plist files are only one example of a type of object that the Plaso tool is
expected to encounter and process.  There can be and are many other parsers
which are designed to process specific data types.

PlistPlugin defines the attributes necessary for registration, discovery
and operation of plugins for plist files which will be used by PlistParser.
"""

from __future__ import unicode_literals

import abc

from plaso.lib import errors
from plaso.parsers import logger
from plaso.parsers import plugins

# pylint: disable=missing-type-doc,missing-return-type-doc
# pylint: disable=missing-yield-doc,missing-yield-type-doc


class PlistPlugin(plugins.BasePlugin):
  """This is an abstract class from which plugins should be based.

  The following are the attributes and methods expected to be overridden by a
  plugin.

  Attributes:
  PLIST_PATH - string of the filename the plugin is designed to process.
  PLIST_KEY - list of keys holding values that are necessary for processing.

  Please note, PLIST_KEY is cAse sensitive and for a plugin to match a
  plist file needs to contain at minimum the number of keys needed for
  processing or WrongPlistPlugin is raised.

  For example if a Plist file contains the following keys,
  {'foo': 1, 'bar': 2, 'opt': 3} with 'foo' and 'bar' being keys critical to
  processing define PLIST_KEY as ['foo', 'bar']. If 'opt' is only optionally
  defined it can still be accessed by manually processing self.top_level from
  the plugin.

  Methods:
  GetEntries() - extract and format info from keys and yields event.PlistEvent.
  """

  NAME = 'plist_plugin'

  # PLIST_PATH is a string for the filename this parser is designed to process.
  # This is expected to be overridden by the processing plugin.
  # Ex. 'com.apple.bluetooth.plist'
  PLIST_PATH = 'any'

  # PLIST_KEYS is a list of keys required by a plugin.
  # This is expected to be overridden by the processing plugin.
  # Ex. frozenset(['DeviceCache', 'PairedDevices'])
  PLIST_KEYS = frozenset(['any'])

  # This is expected to be overridden by the processing plugin.
  # URLS should contain a list of URLs with additional information about
  # this key or value.
  # Ex. ['http://www.forensicswiki.org/wiki/Property_list_(plist)']
  URLS = []

  def _GetKeys(self, top_level, keys, depth=1):
    """Helper function to return keys nested in a plist dict.

    By default this function will return the values for the named keys requested
    by a plugin in match dictionary object. The default setting is to look
    a single layer down from the root (same as the check for plugin
    applicability). This level is suitable for most cases.

    For cases where there is variability in the name at the first level, for
    example the name is the MAC address of a device or a UUID, it is possible
    to override the depth limit and use GetKeys to fetch from a deeper level.

    E.g.
    Top_Level (root):                                             # depth = 0
    -- Key_Name_is_UUID_Generated_At_Install 1234-5678-8          # depth = 1
    ---- Interesting_SubKey_with_value_to_Process: [Values, ...]  # depth = 2

    Args:
      top_level (dict[str, object]): plist top-level key.
      keys: A list of keys that should be returned.
      depth: Defines how many levels deep to check for a match.

    Returns:
      A dictionary with just the keys requested or an empty dict if the plist
      is flat, eg. top_level is a list instead of a dict object.
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
      for _, parsed_key, parsed_value in RecurseKey(top_level, depth=depth):
        if parsed_key in keys:
          match[parsed_key] = parsed_value
          if set(match.keys()) == keys:
            return match
    return match

  # pylint: disable=arguments-differ
  @abc.abstractmethod
  def GetEntries(
      self, parser_mediator, top_level=None, match=None, **unused_kwargs):
    """Extracts event objects from the values of entries within a plist.

    This is the main method that a plist plugin needs to implement.

    The contents of the plist keys defined in PLIST_KEYS will be made available
    to the plugin as self.matched{'KEY': 'value'}. The plugin should implement
    logic to parse this into a useful event for incorporation into the Plaso
    timeline.

    For example if you want to note the timestamps of when devices were
    LastInquiryUpdated you would need to examine the bluetooth config file
    called 'com.apple.bluetooth' and need to look at devices under the key
    'DeviceCache'.  To do this the plugin needs to define
    PLIST_PATH = 'com.apple.bluetooth' and PLIST_KEYS =
    frozenset(['DeviceCache']). IMPORTANT: this interface requires exact names
    and is case sensitive. A unit test based on a real world file is expected
    for each plist plugin.

    When a file with this key is encountered during processing self.matched is
    populated and the plugin's GetEntries() is called.  The plugin would have
    self.matched = {'DeviceCache': [{'DE:AD:BE:EF:01': {'LastInquiryUpdate':
    DateTime_Object}, 'DE:AD:BE:EF:01': {'LastInquiryUpdate':
    DateTime_Object}'...}]} and needs to implement logic here to extract
    values, format, and produce the data as a event.PlistEvent.

    The attributes for a PlistEvent should include the following:
      root = Root key this event was extracted from. E.g. DeviceCache/
      key = Key the value resided in.  E.g. 'DE:AD:BE:EF:01'
      time = Date this artifact was created in number of micro seconds
             (usec) since January 1, 1970, 00:00:00 UTC.
      desc = Short description.  E.g. 'Device LastInquiryUpdated'

    See plist/bluetooth.py for the implemented example plugin.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      top_level (Optional[dict[str, object]]): plist top-level key.
      match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
    """

  def Process(self, parser_mediator, plist_name, top_level, **kwargs):
    """Determine if this is the correct plugin; if so proceed with processing.

    Process() checks if the current plist being processed is a match for a
    plugin by comparing the PATH and KEY requirements defined by a plugin.  If
    both match processing continues; else raise WrongPlistPlugin.

    This function also extracts the required keys as defined in self.PLIST_KEYS
    from the plist and stores the result in self.match[key] and calls
    self.GetEntries() which holds the processing logic implemented by the
    plugin.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      plist_name (str): name of the plist.
      top_level (dict[str, object]): plist top-level key.

    Raises:
      WrongPlistPlugin: If this plugin is not able to process the given file.
      ValueError: If top_level or plist_name are not set.
    """
    if plist_name is None or top_level is None:
      raise ValueError('Top level or plist name are not set.')

    if plist_name.lower() != self.PLIST_PATH.lower():
      raise errors.WrongPlistPlugin(self.NAME, plist_name)

    if isinstance(top_level, dict):
      if not set(top_level.keys()).issuperset(self.PLIST_KEYS):
        raise errors.WrongPlistPlugin(self.NAME, plist_name)

    else:
      # Make sure we are getting back an object that has an iterator.
      if not hasattr(top_level, '__iter__'):
        raise errors.WrongPlistPlugin(self.NAME, plist_name)

      # This is a list and we need to just look at the first level
      # of keys there.
      keys = []
      for top_level_entry in top_level:
        if isinstance(top_level_entry, dict):
          keys.extend(top_level_entry.keys())

      # Compare this is a set, which removes possible duplicate entries
      # in the list.
      if not set(keys).issuperset(self.PLIST_KEYS):
        raise errors.WrongPlistPlugin(self.NAME, plist_name)

    # This will raise if unhandled keyword arguments are passed.
    super(PlistPlugin, self).Process(parser_mediator)

    logger.debug('Plist Plugin Used: {0:s} for: {1:s}'.format(
        self.NAME, plist_name))
    match = self._GetKeys(top_level, self.PLIST_KEYS)
    self.GetEntries(parser_mediator, top_level=top_level, match=match)


# TODO: move to lib.plist.
def RecurseKey(recur_item, depth=15, key_path=''):
  """Flattens nested dictionaries and lists by yielding it's values.

  The hierarchy of a plist file is a series of nested dictionaries and lists.
  This is a helper function helps plugins navigate the structure without
  having to reimplement their own recursive methods.

  This method implements an overridable depth limit to prevent processing
  extremely deeply nested plists. If the limit is reached a debug message is
  logged indicating which key processing stopped on.

  Example Input Plist:
    recur_item = { DeviceRoot: { DeviceMAC1: [Value1, Value2, Value3],
                                 DeviceMAC2: [Value1, Value2, Value3]}}

  Example Output:
    ('', DeviceRoot, {DeviceMACs...})
    (DeviceRoot, DeviceMAC1, [Value1, Value2, Value3])
    (DeviceRoot, DeviceMAC2, [Value1, Value2, Value3])

  Args:
    recur_item: An object to be checked for additional nested items.
    depth: Optional integer indication the current recursion depth.
           This value is used to ensure we stop at the maximum recursion depth.
    key_path: Optional path of the current working key.

  Yields:
    A tuple of the key path, key, and value from a plist.
  """
  if depth < 1:
    logger.debug('Recursion limit hit for key: {0:s}'.format(key_path))
    return

  if isinstance(recur_item, (list, tuple)):
    for recur in recur_item:
      for key in RecurseKey(recur, depth=depth, key_path=key_path):
        yield key
    return

  if not hasattr(recur_item, 'items'):
    return

  for subkey, value in iter(recur_item.items()):
    yield key_path, subkey, value

    if isinstance(value, dict):
      value = [value]

    if isinstance(value, list):
      for item in value:
        if not isinstance(item, dict):
          continue

        subkey_path = '{0:s}/{1:s}'.format(key_path, subkey)
        for tuple_value in RecurseKey(
            item, depth=depth - 1, key_path=subkey_path):
          yield tuple_value
