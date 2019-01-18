# -*- coding: utf-8 -*-
"""The parser and parser plugin presets."""

from __future__ import unicode_literals

import yaml

from plaso.lib import errors


class ParserPreset(object):
  """Parser and parser plugin preset.

  Attributes:
    name (str): name of the preset.
    parsers (list[str]): names of parser and parser plugins.
  """

  def __init__(self, name, parsers):
    """Initializes a parser and parser plugin preset.

    Attributes:
      name (str): name of the preset.
      parsers (list[str]): names of parser and parser plugins.
    """
    super(ParserPreset, self).__init__()
    self.name = name
    self.parsers = parsers


class ParserPresetsManager(object):
  """The parsers and plugin presets manager."""

  def __init__(self):
    """Initializes a parser and parser plugin presets manager."""
    super(ParserPresetsManager, self).__init__()
    self._definitions = {}

  def _ReadParserPresetValues(self, preset_definition_values):
    """Reads a parser preset from a dictionary.

    Args:
      preset_definition_values (dict[str, object]): preset definition values.

    Returns:
      ParserPreset: a parser preset.

    Raises:
      MalformedPresetError: if the format of the preset definition is not set
          or incorrect.
    """
    if not preset_definition_values:
      raise errors.MalformedPresetError('Missing preset definition values.')

    name = preset_definition_values.get('name', None)
    if not name:
      raise errors.MalformedPresetError(
          'Invalid preset definition missing name.')

    parsers = preset_definition_values.get('parsers', None)
    if not parsers:
      raise errors.MalformedPresetError(
          'Invalid preset definition missing parsers.')

    return ParserPreset(name, parsers)

  def _ReadPresetsFromFileObject(self, file_object):
    """Reads parser and parser plugin presets from a file-like object.

    Args:
      file_object (file): file-like object containing the parser and parser
          plugin presets definitions.

    Yields:
      ParserPreset: a parser preset.

    Raises:
      MalformedPresetError: if one or more plugin preset definitions are
          malformed.
    """
    yaml_generator = yaml.safe_load_all(file_object)

    last_preset_definition = None
    for yaml_definition in yaml_generator:
      try:
        preset_definition = self._ReadParserPresetValues(yaml_definition)
      except errors.MalformedPresetError as exception:
        error_location = 'At start'
        if last_preset_definition:
          error_location = 'After: {0:s}'.format(last_preset_definition.name)

        raise errors.MalformedPresetError(
            '{0:s} {1!s}'.format(error_location, exception))

      yield preset_definition
      last_preset_definition = preset_definition

  def GetNames(self):
    """Retrieves the preset names.

    Returns:
      list[str]: preset names in alphabetical order.
    """
    return sorted(self._definitions.keys())

  def GetPresetByName(self, name):
    """Retrieves a specific preset definition by name.

    Args:
      name (str): name of the preset.

    Returns:
      ParserPreset: a parser preset or None if not available.
    """
    return self._definitions.get(name, None)

  def GetPresets(self):
    """Retrieves the preset definitions.

    Yields:
      ParserPreset: parser presets in alphabetical order by name.
    """
    for _, parser_preset in sorted(self._definitions.items()):
      yield parser_preset

  def ReadFromFile(self, path):
    """Reads parser and parser plugin presets from a file.

    Args:
      path (str): path of file that contains the the parser and parser plugin
          presets configuration.
    """
    self._definitions = {}

    with open(path, 'r') as file_object:
      for preset_definition in self._ReadPresetsFromFileObject(file_object):
        self._definitions[preset_definition.name] = preset_definition
