# -*- coding: utf-8 -*-
"""The artifact definitions CLI arguments helper."""

import os

from artifacts import errors as artifacts_errors
from artifacts import reader as artifacts_reader
from artifacts import registry as artifacts_registry

from plaso.cli import tools
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import errors
from plaso.preprocessors import manager as preprocessors_manager


class ArtifactDefinitionsArgumentsHelper(interface.ArgumentsHelper):
  """Artifact definition CLI arguments helper."""

  NAME = u'artifact_definitions'
  DESCRIPTION = u'Artifact definition command line arguments.'

  @classmethod
  def AddArguments(cls, argument_group):
    """Adds command line arguments to an argument group.

    This function takes an argument parser or an argument group object and adds
    to it all the command line arguments this helper supports.

    Args:
      argument_group (argparse._ArgumentGroup|argparse.ArgumentParser):
          argparse group.
    """
    argument_group.add_argument(
        u'--artifact_definitions', u'--artifact-definitions',
        dest=u'artifact_definitions_path', type=str, metavar=u'PATH',
        action=u'store', help=(
            u'Path to a directory containing artifact definitions. Artifact '
            u'definitions can be used to describe and quickly collect data '
            u'data of interest, such as specific files or Windows Registry '
            u'keys.'))

  @classmethod
  def ParseOptions(cls, options, configuration_object):
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options.
      configuration_object (CLITool): object to be configured by the argument
          helper.

    Raises:
      BadConfigObject: when the configuration object is of the wrong type.
      BadConfigOption: if the required artifact definitions are not defined.
    """
    if not isinstance(configuration_object, tools.CLITool):
      raise errors.BadConfigObject(
          u'Configuration object is not an instance of CLITool')

    path = getattr(options, u'artifact_definitions_path', None)

    data_location = getattr(configuration_object, u'_data_location', None)
    if (not path or not os.path.exists(path)) and data_location:
      path = os.path.dirname(data_location)
      path = os.path.join(path, u'artifacts')

    if not path or not os.path.exists(path):
      raise errors.BadConfigOption(
          u'Unable to determine path to artifact definitions.')

    registry = artifacts_registry.ArtifactDefinitionsRegistry()
    reader = artifacts_reader.YamlArtifactsReader()

    try:
      registry.ReadFromDirectory(reader, path)

    except (KeyError, artifacts_errors.FormatError) as exception:
      raise errors.BadConfigOption((
          u'Unable to read artifact definitions from: {0:s} with error: '
          u'{1!s}').format(path, exception))

    for name in preprocessors_manager.PreprocessPluginsManager.GetNames():
      if not registry.GetDefinitionByName(name):
        raise errors.BadConfigOption(
            u'Missing required artifact definition: {0:s}'.format(name))

    setattr(configuration_object, u'_artifacts_registry', registry)


manager.ArgumentHelperManager.RegisterHelper(ArtifactDefinitionsArgumentsHelper)
