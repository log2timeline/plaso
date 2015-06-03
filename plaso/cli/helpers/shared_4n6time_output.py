# -*- coding: utf-8 -*-
"""Arguments helper for information shared between 4n6time output modules."""

from plaso.lib import errors
from plaso.cli.helpers import interface
from plaso.output import shared_4n6time


class Shared4n6TimeOutputHelper(interface.ArgumentsHelper):
  """CLI arguments helper class for 4n6time output modules."""

  NAME = u'4n6time'
  CATEGORY = u'output'
  DESCRIPTION = u'Argument helper for shared 4n6Time output modules.'

  _DEFAULT_FIELDS = [
      u'color', u'datetime', u'host', u'source', u'sourcetype', u'user',
      u'type']

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
        u'--append', dest=u'append', action=u'store_true', default=False,
        required=False, help=(
            u'Defines whether the intention is to append to an already '
            u'existing database or overwrite it. Defaults to overwrite.'))
    argument_group.add_argument(
        u'--evidence', dest=u'evidence', type=unicode, default=u'-',
        action=u'store', required=False, help=(
            u'Set the evidence field to a specific value, defaults to '
            u'empty.'))
    argument_group.add_argument(
        u'--fields', dest=u'fields', type=unicode, action=u'store',
        nargs=u'*', default=None, help=(
            u'Defines which fields should be indexed in the database.'))

  @classmethod
  def ParseOptions(cls, options, output_module):
    """Parses and validates options.

    Args:
      options: the parser option object (instance of argparse.Namespace).
      output_module: an output module (instance of OutputModule).

    Raises:
      BadConfigObject: when the output module object is of the wrong type.
      BadConfigOption: when a configuration parameter fails validation.
    """
    if not isinstance(output_module, shared_4n6time.Base4n6TimeOutputModule):
      raise errors.BadConfigObject(
          u'Output module is not an instance of Base4n6TimeOutputModule')

    append = getattr(options, u'append', False)
    evidence = getattr(options, u'evidence', u'-')

    fields = getattr(options, u'fields', None)
    if not fields:
      fields = cls._DEFAULT_FIELDS

    output_module.SetAppendMode(append)
    output_module.SetEvidence(evidence)
    output_module.SetFields(fields)
