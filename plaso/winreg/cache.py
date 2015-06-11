# -*- coding: utf-8 -*-
"""Interface and plugins for caching of Windows Registry objects."""

import abc

from plaso.lib import errors


class WinRegCachePlugin(object):
  """Class that implements the Window Registry cache plugin interface."""

  ATTRIBUTE = ''

  REG_TYPE = ''
  REG_KEY = u''

  def __init__(self, reg_type):
    """Initialize the plugin.

    Args:
      reg_type: The detected Windows Registry type. This value should match
                the REG_TYPE value defined by the plugins.
    """
    super(WinRegCachePlugin, self).__init__()
    if self.REG_TYPE.lower() != reg_type.lower():
      raise errors.WrongPlugin(u'Not the correct Windows Registry type.')

  def Process(self, registry):
    """Extract the correct key and get the value.

    Args:
      registry: The Windows Registry object (instance of WinRegistry).
    """
    if not self.REG_KEY:
      return

    key = registry.GetKeyByPath(self.REG_KEY)
    if not key:
      return

    return self.GetValue(key)

  @abc.abstractmethod
  def GetValue(self, key):
    """Extract the attribute from the provided key."""


class CurrentControlSetPlugin(WinRegCachePlugin):
  """Class that implements the Current Control Set cache plugin."""

  ATTRIBUTE = 'current_control_set'

  REG_TYPE = 'SYSTEM'
  REG_KEY = u'\\Select'

  def GetValue(self, key):
    """Extract current control set information."""
    value = key.GetValue(u'Current')

    if not value and not value.DataIsInteger():
      return None

    key_number = value.data

    # If the value is Zero then we need to check
    # other keys.
    # The default behavior is:
    #   1. Use the "Current" value.
    #   2. Use the "Default" value.
    #   3. Use the "LastKnownGood" value.
    if key_number == 0:
      default_value = key.GetValue(u'Default')
      lastgood_value = key.GetValue(u'LastKnownGood')

      if default_value and default_value.DataIsInteger():
        key_number = default_value.data

      if not key_number:
        if lastgood_value and lastgood_value.DataIsInteger():
          key_number = lastgood_value.data

    if key_number <= 0 or key_number > 999:
      return None

    return u'ControlSet{0:03d}'.format(key_number)


# TODO: split the cache and the plugin manager.
class WinRegistryCache(object):
  """Class that implements the Windows Registry objects cache.

  There are some values that are valid for the duration of an entire run
  against an image, such as code_page, etc.

  However there are other values that should only be valid for each
  Windows Registry file, such as a current_control_set. The Windows Registry
  objects cache is designed to store those short lived cache values, so they
  can be calculated once for each Windows Registry file, yet do not live
  across all files parsed within an image.

  Attributes:
    attributes: a dictionary of cached attributes and their identifier as key.
  """
  _plugin_classes = {}

  def __init__(self):
    """Initialize the cache object."""
    super(WinRegistryCache, self).__init__()
    self.attributes = {}

  def BuildCache(self, registry, reg_type):
    """Builds up the cache.

    Args:
      registry: The Windows Registry object (instance of WinRegistry).
      reg_type: The Registry type, eg. "SYSTEM", "NTUSER".
    """
    for attribute_name, plugin_class in self._plugin_classes.items():
      try:
        plugin_object = plugin_class(reg_type)

        value = plugin_object.Process(registry)
        if value:
          self.attributes[attribute_name] = value

      except errors.WrongPlugin:
        pass

  @classmethod
  def DeregisterPlugin(cls, plugin_class):
    """Deregisters a plugin class.

    The plugin classes are identified based on their lower case attribute name.

    Args:
      plugin_class: the class object of the plugin.

    Raises:
      KeyError: if plugin class is not set for the corresponding name.
    """
    plugin_name = plugin_class.ATTRIBUTE.lower()
    if plugin_name not in cls._plugin_classes:
      raise KeyError(
          u'Plugin class not set for name: {0:s}.'.format(
              plugin_class.ATTRIBUTE))

    del cls._plugin_classes[plugin_name]

  @classmethod
  def RegisterPlugin(cls, plugin_class):
    """Registers a plugin class.

    The plugin classes are identified based on their lower case attribute name.

    Args:
      plugin_class: the class object of the plugin.

    Raises:
      KeyError: if plugin class is already set for the corresponding name.
    """
    plugin_name = plugin_class.ATTRIBUTE.lower()
    if plugin_name in cls._plugin_classes:
      raise KeyError((
          u'Plugin class already set for name: {0:s}.').format(
              plugin_class.ATTRIBUTE))

    cls._plugin_classes[plugin_name] = plugin_class


WinRegistryCache.RegisterPlugin(CurrentControlSetPlugin)
