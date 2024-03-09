# -*- coding: utf-8 -*-
"""The artifact definitions CLI arguments helper."""

import os
import sys

import artifacts

from artifacts import errors as artifacts_errors
from artifacts import reader as artifacts_reader
from artifacts import registry as artifacts_registry

from plaso.cli import logger
from plaso.cli import tools
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import errors
from plaso.preprocessors import manager as preprocessors_manager


class ArtifactDefinitionsArgumentsHelper(interface.ArgumentsHelper):
  """Artifact definition CLI arguments helper."""

  NAME = 'artifact_definitions'
  DESCRIPTION = 'Artifact definition command line arguments.'

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
        '--artifact_definitions', '--artifact-definitions',
        dest='artifact_definitions_path', type=str, metavar='PATH',
        action='store', help=(
            'Path to a directory or file containing artifact definitions, '
            'which are .yaml files. Artifact definitions can be used to '
            'describe and quickly collect data of interest, such as specific '
            'files or Windows Registry keys.'))

    argument_group.add_argument(
        '--custom_artifact_definitions', '--custom-artifact-definitions',
        dest='custom_artifact_definitions_path', type=str, metavar='PATH',
        action='store', help=(
            'Path to a directory or file containing custom artifact '
            'definitions, which are .yaml files. Artifact definitions can be '
            'used to describe and quickly collect data of interest, such as '
            'specific files or Windows Registry keys.'))

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
          'Configuration object is not an instance of CLITool')

    artifacts_path = getattr(options, 'artifact_definitions_path', None)

    if not artifacts_path or not os.path.exists(artifacts_path):
      artifacts_path = os.path.join(os.path.dirname(artifacts.__file__), 'data')

      if (not os.path.exists(artifacts_path) and
          configuration_object.data_location):
        artifacts_path = os.path.dirname(configuration_object.data_location)
        artifacts_path = os.path.join(artifacts_path, 'artifacts')

      if not os.path.exists(artifacts_path) and 'VIRTUAL_ENV' in os.environ:
        artifacts_path = os.path.join(
            os.environ['VIRTUAL_ENV'], 'share', 'artifacts')

      if not os.path.exists(artifacts_path):
        artifacts_path = os.path.join(sys.prefix, 'share', 'artifacts')
      if not os.path.exists(artifacts_path):
        artifacts_path = os.path.join(sys.prefix, 'local', 'share', 'artifacts')

      if sys.prefix != '/usr':
        if not os.path.exists(artifacts_path):
          artifacts_path = os.path.join('/usr', 'share', 'artifacts')
        if not os.path.exists(artifacts_path):
          artifacts_path = os.path.join('/usr', 'local', 'share', 'artifacts')

      if not os.path.exists(artifacts_path):
        artifacts_path = None

    if not artifacts_path or not os.path.exists(artifacts_path):
      raise errors.BadConfigOption(
          'Unable to determine path to artifact definitions.')

    custom_artifacts_path = getattr(
        options, 'custom_artifact_definitions_path', None)

    if custom_artifacts_path and not os.path.exists(custom_artifacts_path):
      raise errors.BadConfigOption((
          f'Unable to determine path to custom artifact definitions: '
          f'{custom_artifacts_path:s}'))

    if custom_artifacts_path:
      logger.info(
          f'Custom artifact definitions path: {custom_artifacts_path:s}')

    registry = artifacts_registry.ArtifactDefinitionsRegistry()
    reader = artifacts_reader.YamlArtifactsReader()

    logger.info(f'Determined artifact definitions path: {artifacts_path:s}')

    try:
      if os.path.isdir(artifacts_path):
        registry.ReadFromDirectory(reader, artifacts_path)
      else:
        registry.ReadFromFile(reader, artifacts_path)

    except (KeyError, artifacts_errors.FormatError) as exception:
      raise errors.BadConfigOption((
          f'Unable to read artifact definitions from: {artifacts_path:s} '
          f'with error: {exception!s}'))

    if custom_artifacts_path:
      try:
        if os.path.isdir(custom_artifacts_path):
          registry.ReadFromDirectory(reader, custom_artifacts_path)
        else:
          registry.ReadFromFile(reader, custom_artifacts_path)

      except (KeyError, artifacts_errors.FormatError) as exception:
        raise errors.BadConfigOption((
            f'Unable to read custom artifact definitions from: '
            f'{custom_artifacts_path:s} with error: {exception!s}'))

    for name in preprocessors_manager.PreprocessPluginsManager.GetNames():
      artifact_definition = registry.GetDefinitionByName(name)
      if not artifact_definition:
        artifact_definition = registry.GetDefinitionByAlias(name)
      if not artifact_definition:
        raise errors.BadConfigOption(
            f'Missing required artifact definition: {name:s}')

    setattr(configuration_object, '_artifact_definitions_path', artifacts_path)
    setattr(configuration_object, '_custom_artifacts_path',
            custom_artifacts_path)


manager.ArgumentHelperManager.RegisterHelper(ArtifactDefinitionsArgumentsHelper)
