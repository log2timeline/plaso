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
  DESCRIPTION = 'Argument helper for the Elastic Timesketch output modules.'

  _DEFAULT_TIMELINE_ID = 0

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
        '--timeline_id', '--timeline-id', dest='timeline_id', type=int,
        default=cls._DEFAULT_TIMELINE_ID, action='store',
        metavar='TIMELINE_ID', help=(
            'The ID of the Timesketch Timeline object this data is tied to'))

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

    timeline_id = cls._ParseNumericOption(
        options, 'timeline_id', default_value=cls._DEFAULT_TIMELINE_ID)

    if timeline_id:
      output_module.SetTimelineID(timeline_id)


manager.ArgumentHelperManager.RegisterHelper(
    ElasticTimesketchOutputArgumentsHelper)
