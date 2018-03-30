# -*- coding: utf-8 -*-
"""The artifacts filter file CLI arguments helper."""

from __future__ import unicode_literals

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
        dest='artifact_filters', type=str, default=None,
        action='store', help=(
            'Names of forensic artifact definitions, provided in the following'
            'formats. (1) Directly on the command line (comma separated), in a'
            'in a file with one artifact name per line, or one operating system'
            'specific keyword which will process all artifacts supporting that'
            'OS (windows, linux, darwin).  Forensic artifacts are stored '
            'in .yaml files that are directly pulled from the artifact '
            'definitions project. You can also specify a custom artifacts yaml'
            'file (see --custom_artifact_definitions).  Artifact definitions '
            'can be used to describe and quickly collect data of interest, such'
            ' as specific files or Windows Registry keys.'))

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

    artifact_filters = cls._ParseStringOption(
        options, 'artifact_filters').lower()

    if artifact_filters and os.path.isfile(artifact_filters):
      with open(artifact_filters) as f:
        artifact_filters = f.read().splitlines()
    elif artifact_filters:
      artifact_filters = artifact_filters.split(',')

    setattr(configuration_object, '_artifact_filters',
            artifact_filters)


manager.ArgumentHelperManager.RegisterHelper(ArtifactFiltersArgumentsHelper)
