# -*- coding: utf-8 -*-
"""Interface for Apple biome file parser plugins."""
import abc
import blackboxprotobuf

from plaso.parsers import plugins


class AppleBiomePlugin(plugins.BasePlugin):
  """Apple biome (aka SEGB) file parser plugin."""

  NAME = 'biome_plugins'
  DATA_FORMAT = 'apple biome'

  REQUIRED_SCHEMA = None

  def CheckRequiredSchema(self, protobuf):
    """Checks if the record of an Aple biome file has the required schema by the
    plugin.

    Args:
      protobuf (bytes): Content of the protobuf field in the Apple biome record.
    Returns:
      bool: True if the record's protobuf's schema is valid.
    """
    if not self.REQUIRED_SCHEMA:
      return False

    _, schema = blackboxprotobuf.decode_message(protobuf)

    if schema.items() <= self.REQUIRED_SCHEMA.items():
      return True

    return False

  # pylint: disable=arguments-differ
  @abc.abstractmethod
  def Process(self, parser_mediator, biome_file=None, **unused_kwargs):
    """Extracts information from an Apple biome file. This is the main method
    that an Apple biome file plugin needs to implement.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      biome_file (Optional[AppleBiomeFile]): Apple biome file.

    Raises:
      ValueError: If the file_object value is missing.
    """
