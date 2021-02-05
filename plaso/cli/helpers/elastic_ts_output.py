# -*- coding: utf-8 -*-
"""The Elastic Timesketch output module CLI arguments helper."""

from plaso.cli.helpers import elastic_output
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import errors
from plaso.output import elastic_ts


class ElasticTimesketchOutputArgumentsHelper(interface.ArgumentsHelper):
  """Elastic Timesketch output module CLI arguments helper."""

  NAME = 'elastic_ts'
  CATEGORY = 'output'
  DESCRIPTION = 'Argument helper for the Elastic Timesketch output module.'

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
    elastic_output.ElasticSearchOutputArgumentsHelper.AddArguments(
        argument_group)

    argument_group.add_argument(
        '--timeline_identifier', '--timeline-identifier',
        dest='timeline_identifier', type=int,
        default=cls._DEFAULT_TIMELINE_IDENTIFIER, action='store',
        metavar='IDENTIFIER', help=(
             'The identifier of the timeline in Timesketch.'))

  # pylint: disable=arguments-differ
  @classmethod
  def ParseOptions(cls, options, output_module):
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options.
      output_module (OutputModule): output module to configure.

    Raises:
      BadConfigObject: when the output module object is of the wrong type.
      BadConfigOption: when a configuration parameter fails validation.
    """
    if not isinstance(
        output_module, elastic_ts.ElasticTimesketchOutputModule):
      raise errors.BadConfigObject(
          'Output module is not an instance of ElasticsearchOutputModule')

    elastic_output.ElasticSearchOutputArgumentsHelper.ParseOptions(
        options, output_module)

    timeline_identifier = cls._ParseNumericOption(
        options, 'timeline_identifier',
        default_value=cls._DEFAULT_TIMELINE_IDENTIFIER)

    if timeline_identifier:
      output_module.SetTimelineIdentifier(timeline_identifier)


manager.ArgumentHelperManager.RegisterHelper(
    ElasticTimesketchOutputArgumentsHelper)
