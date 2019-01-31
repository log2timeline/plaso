# -*- coding: utf-8 -*-
"""The parser and parser plugin presets."""

from __future__ import unicode_literals

import yaml

from plaso.containers import artifacts
from plaso.lib import errors


class ParserPreset(object):
  """Parser and parser plugin preset.

  Attributes:
    name (str): name of the preset.
    operating_systems (list[OperatingSystemArtifact]): operating system
        artifact attribute containers, that specify to which operating
        systems the preset applies.
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
    self.operating_systems = []
    self.parsers = parsers


class ParserPresetsManager(object):
  """The parsers and plugin presets manager."""

  def __init__(self):
    """Initializes a parser and parser plugin presets manager."""
    super(ParserPresetsManager, self).__init__()
    self._definitions = {}

  def _ReadOperatingSystemArtifactValues(self, operating_system_values):
    """Reads an operating system artifact from a dictionary.

    Args:
      operating_system_values (dict[str, object]): operating system values.

    Returns:
      OperatingSystemArtifact: an operating system artifact attribute container.

    Raises:
      MalformedPresetError: if the format of the operating system values are
          not set or incorrect.
    """
    if not operating_system_values:
      raise errors.MalformedPresetError('Missing operating system values.')

    family = operating_system_values.get('family', None)
    product = operating_system_values.get('product', None)
    version = operating_system_values.get('version', None)

    if not family and not product:
      raise errors.MalformedPresetError(
          'Invalid operating system missing family and product.')

    return artifacts.OperatingSystemArtifact(
        family=family, product=product, version=version)

  def _ReadParserPresetValues(self, preset_definition_values):
    """Reads a parser preset from a dictionary.

    Args:
      preset_definition_values (dict[str, object]): preset definition values.

    Returns:
      ParserPreset: a parser preset.

    Raises:
      MalformedPresetError: if the format of the preset definition is not set
          or incorrect, or the preset of a specific operating system has already
          been set.
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

    parser_preset = ParserPreset(name, parsers)

    for operating_system_values in preset_definition_values.get(
        'operating_systems', []):
      operating_system = self._ReadOperatingSystemArtifactValues(
          operating_system_values)
      parser_preset.operating_systems.append(operating_system)

    return parser_preset

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
    name = name.lower()
    return self._definitions.get(name, None)

  def GetPresetsByOperatingSystem(self, operating_system):
    """Retrieves preset definitions for a specific operating system.

    Args:
      operating_system (OperatingSystemArtifact): an operating system artifact
          attribute container.

    Returns:
      list[PresetDefinition]: preset definition that correspond with the
          operating system.
    """
    preset_definitions = []
    for preset_definition in self._definitions.values():
      for preset_operating_system in preset_definition.operating_systems:
        if preset_operating_system.IsEquivalent(operating_system):
          preset_definitions.append(preset_definition)

    return preset_definitions

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
