# -*- coding: utf-8 -*-
"""The artifacts filter file CLI arguments helper."""

import os

from plaso.cli import tools
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import errors


class ArtifactFiltersArgumentsHelper(interface.ArgumentsHelper):
  """Artifacts filter file CLI arguments helper."""

  NAME = 'artifact_filters'
  DESCRIPTION = 'Artifact filters command line arguments.'

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
        '--artifact_filters', '--artifact-filters',
        dest='artifact_filter_string', type=str, default=None,
        metavar='ARTIFACT_FILTERS', action='store', help=(
            'Names of forensic artifact definitions, provided on the command '
            'command line (comma separated). Forensic artifacts are stored '
            'in .yaml files that are directly pulled from the artifact '
            'definitions project. You can also specify a custom '
            'artifacts yaml file (see --custom_artifact_definitions). Artifact '
            'definitions can be used to describe and quickly collect data of '
            'interest, such as specific files or Windows Registry keys.'))

    argument_group.add_argument(
        '--artifact_filters_file', '--artifact-filters_file',
        dest='artifact_filters_file', type=str, default=None,
        metavar='PATH', action='store', help=(
            'Names of forensic artifact definitions, provided in a file with '
            'one artifact name per line. Forensic artifacts are stored in '
            '.yaml files that are directly pulled from the artifact '
            'definitions project. You can also specify a custom artifacts '
            'yaml file (see --custom_artifact_definitions). Artifact '
            'definitions can be used to describe and quickly collect data of '
            'interest, such as specific files or Windows Registry keys.'))

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

    artifact_filters = cls._ParseStringOption(options, 'artifact_filter_string')
    artifact_filters_file = cls._ParseStringOption(
        options, 'artifact_filters_file')
    filter_file = cls._ParseStringOption(options, 'file_filter')

    if artifact_filters and artifact_filters_file:
      raise errors.BadConfigOption(
          'Please only specify artifact definition names in a file '
          'or on the command line.')

    if (artifact_filters_file or artifact_filters) and filter_file:
      raise errors.BadConfigOption(
          'Please do not specify both artifact definitions and legacy filters.')

    if artifact_filters_file and os.path.isfile(artifact_filters_file):
      with open(artifact_filters_file, 'r', encoding='utf-8') as file_object:
        file_content = file_object.read()
        artifact_filters = file_content.splitlines()

    elif artifact_filters:
      artifact_filters = [name.strip() for name in artifact_filters.split(',')]

    setattr(configuration_object, '_artifact_filters', artifact_filters)


manager.ArgumentHelperManager.RegisterHelper(ArtifactFiltersArgumentsHelper)
