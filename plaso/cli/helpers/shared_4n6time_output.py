# -*- coding: utf-8 -*-
"""The 4n6time output modules shared CLI arguments helper."""

from plaso.lib import errors
from plaso.cli.helpers import interface
from plaso.output import shared_4n6time


class Shared4n6TimeOutputArgumentsHelper(interface.ArgumentsHelper):
  """4n6time output modules shared CLI arguments helper."""

  NAME = u'4n6time'
  CATEGORY = u'output'
  DESCRIPTION = u'Argument helper for shared 4n6Time output modules.'

  _DEFAULT_APPEND = False
  _DEFAULT_EVIDENCE = u'-'
  _DEFAULT_FIELDS = u','.join([
      u'datetime', u'host', u'source', u'sourcetype', u'user', u'type'])

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
        u'--append', dest=u'append', action=u'store_true', default=False,
        required=cls._DEFAULT_APPEND, help=(
            u'Defines whether the intention is to append to an already '
            u'existing database or overwrite it. Defaults to overwrite.'))
    argument_group.add_argument(
        u'--evidence', dest=u'evidence', type=str,
        default=cls._DEFAULT_EVIDENCE, action=u'store', required=False,
        help=u'Set the evidence field to a specific value, defaults to empty.')
    argument_group.add_argument(
        u'--fields', dest=u'fields', type=str, action=u'store',
        default=cls._DEFAULT_FIELDS, help=(
            u'Defines which fields should be indexed in the database.'))
    argument_group.add_argument(
        u'--additional_fields', dest=u'additional_fields', type=str,
        action=u'store', default=u'', help=(
            u'Defines extra fields to be included in the output, in addition to'
            u' the default fields, which are {0:s}.'.format(
                cls._DEFAULT_FIELDS)))

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
          u'Output module is not an instance of Shared4n6TimeOutputModule')

    append = getattr(options, u'append', cls._DEFAULT_APPEND)
    evidence = cls._ParseStringOption(
        options, u'evidence', default_value=cls._DEFAULT_EVIDENCE)
    fields = cls._ParseStringOption(
        options, u'fields', default_value=cls._DEFAULT_FIELDS)
    additional_fields = cls._ParseStringOption(
        options, u'additional_fields')

    if additional_fields:
      fields = u'{0:s},{1:s}'.format(fields, additional_fields)

    output_module.SetAppendMode(append)
    output_module.SetEvidence(evidence)
    output_module.SetFields([
        field_name.strip() for field_name in fields.split(u',')])
