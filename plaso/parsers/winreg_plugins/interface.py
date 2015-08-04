# -*- coding: utf-8 -*-
"""The Windows Registry plugin objects interface."""

import abc
import logging

from plaso.dfwinreg import path_expander as dfwinreg_path_expander
from plaso.parsers import plugins


class RegistryPlugin(plugins.BasePlugin):
  """Class that defines the Windows Registry plugin object interface."""

  NAME = u'winreg'
  DESCRIPTION = u'Parser for Registry data.'

  # Indicate the type of hive this plugin belongs to (eg. NTUSER, SOFTWARE).
  REG_TYPE = u'any'

  # URLS should contain a list of URLs with additional information about this
  # key or value.
  URLS = []

  # WEIGHT is a simple integer value representing the priority of this plugin.
  # The weight can be used by some parser implementation to prioritize the
  # order in which plugins are run against the Windows Registry keys.
  # By default no the Windows Registry plugin should overwrite this value,
  # it should only be defined in interfaces extending the base class, providing
  # higher level of prioritization to Windows Registry plugins.
  WEIGHT = 3

  @abc.abstractmethod
  def GetEntries(
      self, parser_mediator, key=None, registry_file_type=None,
      codepage=u'cp1252', **kwargs):
    """Extracts event objects from the Windows Registry key.

    Args:
      parser_mediator: A parser context object (instance of ParserContext).
      key: Optional Registry key (instance of dfwinreg.WinRegKey).
           The default is None.
      registry_file_type: Optional string containing the Windows Registry file
                          type, e.g. NTUSER, SOFTWARE. The default is None.
      codepage: Optional extended ASCII string codepage. The default is cp1252.
    """

  def Process(self, parser_mediator, key=None, **kwargs):
    """Processes a Windows Registry key or value.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: Optional Registry key (instance of dfwinreg.WinRegKey).
           The default is None.

    Raises:
      ValueError: If the key value is not set.
    """
    if key is None:
      raise ValueError(u'Key is not set.')

    del kwargs[u'registry_file_type']
    del kwargs[u'codepage']

    # This will raise if unhandled keyword arguments are passed.
    super(RegistryPlugin, self).Process(parser_mediator)


class KeyPlugin(RegistryPlugin):
  """Class that defines the Windows Registry key-based plugin interface.

  Attributes:
    expanded_keys: a list of expanded key paths or None.
  """

  # A list of all the Windows Registry key paths this plugins supports.
  # Each of these key paths can contain a path that needs to be expanded,
  # such as {current_control_set}, etc.
  REG_KEYS = []

  WEIGHT = 1

  def __init__(self):
    """Initializes key-based Windows Registry plugin object."""
    super(KeyPlugin, self).__init__()
    self._path_expander = dfwinreg_path_expander.WinRegistryKeyPathExpander()
    self.expanded_keys = None

  def ExpandKeys(self, parser_mediator):
    """Builds a list of expanded keys this plugin supports.

    Args:
      parser_mediator: A parser context object (instance of ParserContext).
    """
    self.expanded_keys = []
    for key_path in self.REG_KEYS:
      # TODO: replace this with HKEY_LOCAL_MACHINE\\System\\CurrentControlSet
      if key_path.startswith(u'\\{current_control_set}'):
        # TODO: get control set keys.
        pass

      # TODO: replace by current_control_set expansion.
      expanded_key = u''
      try:
        # TODO: deprecate direct use of pre_obj.
        expanded_key = self._path_expander.ExpandPath(
            key_path, pre_obj=parser_mediator.knowledge_base.pre_obj)
      except KeyError as exception:
        logging.debug((
            u'Unable to expand Registry key {0:s} for plugin {1:s} with '
            u'error: {2:s}').format(key_path, self.NAME, exception))
        continue

      if not expanded_key:
        continue

      self.expanded_keys.append(expanded_key)

      # Special case of Wow6432 Windows Registry redirection.
      # URL: http://msdn.microsoft.com/en-us/library/windows/desktop/\
      # ms724072%28v=vs.85%29.aspx
      if expanded_key.startswith(u'\\Software'):
        _, first, second = expanded_key.partition(u'\\Software')
        self.expanded_keys.append(u'{0:s}\\Wow6432Node{1:s}'.format(
            first, second))

      if self.REG_TYPE in [u'any', u'SOFTWARE']:
        self.expanded_keys.append(u'\\Wow6432Node{0:s}'.format(expanded_key))

  @abc.abstractmethod
  def GetEntries(
      self, parser_mediator, key=None, registry_file_type=None,
      codepage=u'cp1252', **kwargs):
    """Extracts event objects from the Windows Registry key.

    Args:
      parser_mediator: A parser context object (instance of ParserContext).
      key: Optional Registry key (instance of dfwinreg.WinRegKey).
           The default is None.
      registry_file_type: Optional string containing the Windows Registry file
                          type, e.g. NTUSER, SOFTWARE. The default is None.
      codepage: Optional extended ASCII string codepage. The default is cp1252.
    """

  def Process(
      self, parser_mediator, key=None, registry_file_type=None,
      codepage=u'cp1252', **kwargs):
    """Processes a Windows Registry key.

    Args:
      parser_mediator: A parser context object (instance of ParserContext).
      key: Optional Registry key (instance of dfwinreg.WinRegKey).
           The default is None.
      registry_file_type: Optional string containing the Windows Registry file
                          type, e.g. NTUSER, SOFTWARE. The default is None.
      codepage: Optional extended ASCII string codepage. The default is cp1252.
    """
    if self.expanded_keys is None:
      self.ExpandKeys(parser_mediator)

    super(KeyPlugin, self).Process(
        parser_mediator, key=key, registry_file_type=registry_file_type,
        codepage=codepage)

    if key and key.path in self.expanded_keys:
      self.GetEntries(
          parser_mediator, key=key, registry_file_type=registry_file_type,
          **kwargs)


class ValuePlugin(RegistryPlugin):
  """Class that defines the Windows Registry value-based plugin interface."""

  # REG_VALUES should be defined as a frozenset.
  REG_VALUES = frozenset()

  WEIGHT = 2

  @abc.abstractmethod
  def GetEntries(
      self, parser_mediator, key=None, registry_file_type=None,
      codepage=u'cp1252', **kwargs):
    """Extracts event objects from the Windows Registry key.

    Args:
      parser_mediator: A parser context object (instance of ParserContext).
      key: Optional Registry key (instance of dfwinreg.WinRegKey).
           The default is None.
      registry_file_type: Optional string containing the Windows Registry file
                          type, e.g. NTUSER, SOFTWARE. The default is None.
      codepage: Optional extended ASCII string codepage. The default is cp1252.
    """

  def Process(
      self, parser_mediator, key=None, registry_file_type=None,
      codepage=u'cp1252', **kwargs):
    """Processes a Windows Registry value.

    Args:
      parser_mediator: A parser context object (instance of ParserContext).
      key: Optional Registry key (instance of dfwinreg.WinRegKey).
           The default is None.
      registry_file_type: Optional string containing the Windows Registry file
                          type, e.g. NTUSER, SOFTWARE. The default is None.
      codepage: Optional extended ASCII string codepage. The default is cp1252.
    """
    super(ValuePlugin, self).Process(
        parser_mediator, key=key, registry_file_type=registry_file_type,
        codepage=codepage)

    values = frozenset([value.name for value in key.GetValues()])
    if self.REG_VALUES.issubset(values):
      self.GetEntries(
          parser_mediator, key=key, registry_file_type=registry_file_type,
          codepage=codepage, **kwargs)
