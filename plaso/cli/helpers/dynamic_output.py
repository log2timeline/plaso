# -*- coding: utf-8 -*-
"""The arguments helper for the dynamic output module."""

from plaso.lib import errors
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.output import dynamic


class DynamicOutputHelper(interface.ArgumentsHelper):
  """CLI arguments helper class for the dynamic output module."""

  NAME = u'dynamic'
  CATEGORY = u'output'
  DESCRIPTION = u'Argument helper for the dynamic output module.'

  _DEFAULT_FIELDS = [
      u'datetime', u'timestamp_desc', u'source', u'source_long',
      u'message', u'parser', u'display_name', u'tag']

  @classmethod
  def AddArguments(cls, argument_group):
    """Add command line arguments the helper supports to an argument group.

    This function takes an argument parser or an argument group object and adds
    to it all the command line arguments this helper supports.

    Args:
      argument_group: the argparse group (instance of argparse._ArgumentGroup or
                      or argparse.ArgumentParser).
    """
    argument_group.add_argument(
        u'--fields', dest=u'fields', type=str, action=u'store',
        nargs=u'*', default=u','.join(cls._DEFAULT_FIELDS),
        help=u'Defines which fields should be included in the output.')

  @classmethod
  def ParseOptions(cls, options, output_module):
    """Parses and validates options.

    Args:
      options: the parser option object (instance of argparse.Namespace).
      output_module: an output module (instance of OutputModule).

    Raises:
      BadConfigObject: when the output module object is of the wrong type.
      BadConfigOption: when the output filename was not provided.
    """
    if not isinstance(output_module, dynamic.DynamicOutputModule):
      raise errors.BadConfigObject(
          u'Output module is not an instance of DynamicOutputModule')

    fields = cls._ParseStringOption(
        options, u'fields', default_value=cls._DEFAULT_FIELDS)

    output_module.SetFields([
        field_name.strip() for field_name in fields.split(u',')])


manager.ArgumentHelperManager.RegisterHelper(DynamicOutputHelper)
