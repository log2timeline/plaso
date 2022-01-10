# -*- coding: utf-8 -*-
"""The OpenSearch Timesketch output module CLI arguments helper."""

from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.cli.helpers import opensearch_output
from plaso.lib import errors
from plaso.output import opensearch_ts


class OpenSearchTimesketchOutputArgumentsHelper(interface.ArgumentsHelper):
  """OpenSearch Timesketch output module CLI arguments helper."""

  NAME = 'opensearch_ts'
  CATEGORY = 'output'
  DESCRIPTION = 'Argument helper for the OpenSearch Timesketch output module.'

  _DEFAULT_TIMELINE_IDENTIFIER = 0

  @classmethod
  def AddArguments(cls, argument_group):
    """Adds command line arguments the helper supports to an argument group.

    This function takes an argument parser or an argument group object and adds
    to it all the command line arguments this helper supports.

    Args:
      argument_group (argparse._ArgumentGroup|argparse.ArgumentParser):
          argparse group.
    """
    opensearch_output.OpenSearchOutputArgumentsHelper.AddArguments(
        argument_group)

    argument_group.add_argument(
        '--timeline_identifier', '--timeline-identifier',
        dest='timeline_identifier', type=int,
        default=cls._DEFAULT_TIMELINE_IDENTIFIER, action='store',
        metavar='IDENTIFIER', help=(
             'The identifier of the timeline in Timesketch.'))

  @classmethod
  def ParseOptions(cls, options, output_module):  # pylint: disable=arguments-renamed
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options.
      output_module (OutputModule): output module to configure.

    Raises:
      BadConfigObject: when the output module object is of the wrong type.
      BadConfigOption: when a configuration parameter fails validation.
    """
    if not isinstance(
        output_module, opensearch_ts.OpenSearchTimesketchOutputModule):
      raise errors.BadConfigObject(
          'Output module is not an instance of OpenSearchsearchOutputModule')

    opensearch_output.OpenSearchOutputArgumentsHelper.ParseOptions(
        options, output_module)

    timeline_identifier = cls._ParseNumericOption(
        options, 'timeline_identifier',
        default_value=cls._DEFAULT_TIMELINE_IDENTIFIER)

    if timeline_identifier:
      output_module.SetTimelineIdentifier(timeline_identifier)


manager.ArgumentHelperManager.RegisterHelper(
    OpenSearchTimesketchOutputArgumentsHelper)
