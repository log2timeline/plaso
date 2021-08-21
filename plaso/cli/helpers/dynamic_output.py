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

  _DEFAULT_FIELDS = [
      'datetime', 'timestamp_desc', 'source', 'source_long',
      'message', 'parser', 'display_name', 'tag']

  @classmethod
  def AddArguments(cls, argument_group):
    """Adds command line arguments the helper supports to an argument group.

    This function takes an argument parser or an argument group object and adds
    to it all the command line arguments this helper supports.

    Args:
      argument_group (argparse._ArgumentGroup|argparse.ArgumentParser):
          argparse group.
    """
    default_fields = ','.join(cls._DEFAULT_FIELDS)
    argument_group.add_argument(
        '--fields', dest='fields', type=str, action='store',
        default=default_fields, help=(
            'Defines which fields should be included in the output.'))

    default_fields = ', '.join(cls._DEFAULT_FIELDS)
    argument_group.add_argument(
        '--additional_fields', '--additional-fields', dest='additional_fields',
        type=str, action='store', default='', help=(
            'Defines extra fields to be included in the output, in addition to '
            'the default fields, which are {0:s}.'.format(default_fields)))

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

    default_fields = ','.join(cls._DEFAULT_FIELDS)
    fields = cls._ParseStringOption(
        options, 'fields', default_value=default_fields)

    additional_fields = cls._ParseStringOption(options, 'additional_fields')
    if additional_fields:
      fields = ','.join([fields, additional_fields])

    output_module.SetFields([
        field_name.strip() for field_name in fields.split(',')])


manager.ArgumentHelperManager.RegisterHelper(DynamicOutputArgumentsHelper)
