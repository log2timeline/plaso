# -*- coding: utf-8 -*-
"""The parser and parser plugin presets."""

from __future__ import unicode_literals

import yaml

from plaso.lib import errors


class ParserPresetDefinition(object):
  """Parser and parser plugin preset definition.

  Attributes:
    name (str): name of the preset.
    parsers (list[str]): names of parser and parser plugins.
  """

  def __init__(self, name, parsers):
    """Initializes a parser and parser plugin preset definition.

    Attributes:
      name (str): name of the preset.
      parsers (list[str]): names of parser and parser plugins.
    """
    super(ParserPresetDefinition, self).__init__()
    self.name = name
    self.parsers = parsers


class ParserPresets(object):
  """Parser and parser plugin presets."""

  def __init__(self):
    """Initializes parser and parser plugin presets."""
    super(ParserPresets, self).__init__()
    self._definitions = {}

  def _ReadPresetDefinitionValues(self, preset_definition_values):
    """Reads a preset definition from a dictionary.

    Args:
      preset_definition_values (dict[str, object]): preset definition values.

    Returns:
      ParserPresetDefinition: a preset definition.

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

    return ParserPresetDefinition(name, parsers)

  def _ReadPresetsFromFileObject(self, file_object):
    """Reads parser and parser plugin presets from a file-like object.

    Args:
      file_object (file): file-like object containing the parser and parser
          plugin presets definitions.

    Yields:
      PresetDefinition: preset definition.

    Raises:
      MalformedPresetError: if one or more plugin preset definitions are
          malformed.
    """
    yaml_generator = yaml.safe_load_all(file_object)

    last_preset_definition = None
    for yaml_definition in yaml_generator:
      try:
        preset_definition = self._ReadPresetDefinitionValues(yaml_definition)
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
      PresetDefinition: preset definition or None if not available.
    """
    return self._definitions.get(name, None)

  def GetPresets(self):
    """Retrieves the preset definitions.

    Yields:
      PresetDefinition: preset definition in alphabetical order by name.
    """
    for _, preset_definition in sorted(self._definitions.items()):
      yield preset_definition

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
