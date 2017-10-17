# -*- coding: utf-8 -*-
"""The 4n6time output modules shared CLI arguments helper."""

from __future__ import unicode_literals

from plaso.lib import errors
from plaso.cli.helpers import interface
from plaso.output import shared_4n6time


class Shared4n6TimeOutputArgumentsHelper(interface.ArgumentsHelper):
  """4n6time output modules shared CLI arguments helper."""

  NAME = '4n6time'
  CATEGORY = 'output'
  DESCRIPTION = 'Argument helper for shared 4n6Time output modules.'

  _DEFAULT_APPEND = False
  _DEFAULT_EVIDENCE = '-'
  _DEFAULT_FIELDS = ','.join([
      'datetime', 'host', 'source', 'sourcetype', 'user', 'type'])

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
        '--append', dest='append', action='store_true', default=False,
        required=cls._DEFAULT_APPEND, help=(
            'Defines whether the intention is to append to an already '
            'existing database or overwrite it. Defaults to overwrite.'))
    argument_group.add_argument(
        '--evidence', dest='evidence', type=str,
        default=cls._DEFAULT_EVIDENCE, action='store', required=False,
        help='Set the evidence field to a specific value, defaults to empty.')
    argument_group.add_argument(
        '--fields', dest='fields', type=str, action='store',
        default=cls._DEFAULT_FIELDS, help=(
            'Defines which fields should be indexed in the database.'))
    argument_group.add_argument(
        '--additional_fields', dest='additional_fields', type=str,
        action='store', default='', help=(
            'Defines extra fields to be included in the output, in addition to'
            ' the default fields, which are {0:s}.'.format(
                cls._DEFAULT_FIELDS)))

  # pylint: disable=arguments-differ
  @classmethod
  def ParseOptions(cls, options, output_module):
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options.
      output_module (OutputModule): output module to configure.

    Raises:
      BadConfigObject: when the output module object is of the wrong type.
    """
    if not isinstance(output_module, shared_4n6time.Shared4n6TimeOutputModule):
      raise errors.BadConfigObject(
          'Output module is not an instance of Shared4n6TimeOutputModule')

    append = getattr(options, 'append', cls._DEFAULT_APPEND)
    evidence = cls._ParseStringOption(
        options, 'evidence', default_value=cls._DEFAULT_EVIDENCE)
    fields = cls._ParseStringOption(
        options, 'fields', default_value=cls._DEFAULT_FIELDS)
    additional_fields = cls._ParseStringOption(
        options, 'additional_fields')

    if additional_fields:
      fields = '{0:s},{1:s}'.format(fields, additional_fields)

    output_module.SetAppendMode(append)
    output_module.SetEvidence(evidence)
    output_module.SetFields([
        field_name.strip() for field_name in fields.split(',')])
