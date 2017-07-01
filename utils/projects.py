# -*- coding: utf-8 -*-
"""Helper for project configuration."""

from __future__ import print_function

try:
  import ConfigParser as configparser
except ImportError:
  import configparser  # pylint: disable=import-error


class ProjectDefinition(object):
  """Project definition.

  Attributes:
    description_long (str): long description.
    description_short (str): short description.
    homepage_url (str): URL of the homepage.
    maintainer (str): maintainer.
    name (str): name of the project.
  """

  def __init__(self):
    """Initializes a project configuation."""
    super(ProjectDefinition, self).__init__()
    self.description_long = None
    self.description_short = None
    self.homepage_url = None
    self.maintainer = None
    self.name = None


class ProjectDefinitionReader(object):
  """Project definition reader."""

  _VALUE_NAMES = frozenset([
      u'description_long',
      u'description_short',
      u'homepage_url',
      u'maintainer',
      u'name'])

  def _GetConfigValue(self, config_parser, section_name, value_name):
    """Retrieves a value from the config parser.

    Args:
      config_parser (ConfigParser): configuration parser.
      section_name (str): name of the section that contains the value.
      value_name (str): name of the value.

    Returns:
      object: value or None if the value does not exists.
    """
    try:
      return config_parser.get(section_name, value_name)
    except configparser.NoOptionError:
      return

  def Read(self, file_object):
    """Reads project definitions.

    Args:
      file_object (file): file-like object to read from.

    Returns:
      ProjectDefinition: project definition.
    """
    config_parser = configparser.RawConfigParser()
    config_parser.readfp(file_object)

    project_definition = ProjectDefinition()
    for value_name in self._VALUE_NAMES:
      value = self._GetConfigValue(config_parser, u'project', value_name)
      setattr(project_definition, value_name, value)

    return project_definition
