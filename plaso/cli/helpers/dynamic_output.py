# -*- coding: utf-8 -*-
"""The dynamic output module CLI arguments helper."""

from plaso.lib import errors
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.output import dynamic


class DynamicOutputArgumentsHelper(interface.ArgumentsHelper):
  """Dynamic output module CLI arguments helper."""

  NAME = 'dynamic'
  CATEGORY = 'output'
  DESCRIPTION = 'Argument helper for the dynamic output module.'

  _DEFAULT_FIELDS = ','.join([
      'datetime', 'timestamp_desc', 'source', 'source_long',
      'message', 'parser', 'display_name', 'tag'])

  @classmethod
  def AddArguments(cls, argument_group):
    """Adds command line arguments the helper supports to an argument group.

    This function takes an argument parser or an argument group object and adds
    to it all the command line arguments this helper supports.

    Args:
      argument_group (argparse._ArgumentGroup|argparse.ArgumentParser):
          argparse group.
    """
    argument_group.add_argument(
        '--fields', dest='fields', type=str, action='store',
        default=cls._DEFAULT_FIELDS, help=(
            'Defines which fields should be included in the output.'))

  @classmethod
  def ParseOptions(cls, options, output_module):  # pylint: disable=arguments-renamed
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options.
      output_module (OutputModule): output module to configure.

    Raises:
      BadConfigObject: when the output module object is of the wrong type.
      BadConfigOption: when the output filename was not provided.
    """
    if not isinstance(output_module, dynamic.DynamicOutputModule):
      raise errors.BadConfigObject(
          'Output module is not an instance of DynamicOutputModule')

    fields = cls._ParseStringOption(
        options, 'fields', default_value=cls._DEFAULT_FIELDS)

    output_module.SetFields([name.strip() for name in fields.split(',')])


manager.ArgumentHelperManager.RegisterHelper(DynamicOutputArgumentsHelper)
