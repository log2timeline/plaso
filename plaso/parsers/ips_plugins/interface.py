# -*- coding: utf-8 -*-
"""Interface for IPS log file parser plugins."""
import abc

from plaso.parsers import plugins


class IPSPlugin(plugins.BasePlugin):
  """IPS file parser plugin."""

  NAME = 'ips_plugin'
  DATA_FORMAT = 'ips log file'

  REQUIRED_HEADER_KEYS = []
  REQUIRED_CONTENT_KEYS = []

  def CheckRequiredKeys(self, ips_file):
    """Checks if the ips file's header and content have the keys required by
    the plugin.
    Args:
      ips_file (IPSFile): the file for which the structure is checked.
    Returns:
      bool: True if the file has the required keys defined by the plugin, or
          False if it does not, or if the plugin does not define required
          keys. The header and content can have more keys than the minimum
          required and still return True.
    """
    if not self.REQUIRED_HEADER_KEYS or not self.REQUIRED_CONTENT_KEYS:
      return False

    has_required_keys = True
    for required_header_key in self.REQUIRED_HEADER_KEYS:
      if required_header_key not in ips_file.header.keys():
        has_required_keys = False
        break

    for required_content_key in self.REQUIRED_CONTENT_KEYS:
      if required_content_key not in ips_file.content.keys():
        has_required_keys = False
        break

    return has_required_keys

  # pylint: disable=arguments-differ
  @abc.abstractmethod
  def Process(self, parser_mediator, ips_file=None, **unused_kwargs):
    """Extracts information from an ips log file.
    This is the main method that an ips plugin needs to implement.
    Args:
      parser_mediator (ParserMediator): parser mediator.
      ips_file (Optional[IPSFile]): database.
    Raises:
      ValueError: If the file value is missing.
    """
