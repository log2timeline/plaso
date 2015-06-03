# -*- coding: utf-8 -*-
"""The arguments helper for the timesketch output module."""

import uuid

from plaso.lib import errors
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.output import timesketch_out


class TimesketchOutputHelper(interface.ArgumentsHelper):
  """CLI arguments helper class for a timesketch output module."""

  NAME = u'timesketch'
  CATEGORY = u'output'
  DESCRIPTION = u'Argument helper for the timesketch output module.'

  @classmethod
  def AddArguments(cls, argument_group):
    """Add command line arguments the helper supports to an argument group.

    This function takes an argument parser or an argument group object and adds
    to it all the command line arguments this helper supports.

    Args:
      argument_group: the argparse group (instance of argparse._ArgumentGroup or
                      or argparse.ArgumentParser).
    """
    default_uid = uuid.uuid4().hex

    argument_group.add_argument(
        u'--name', u'--timeline_name', u'--timeline-name',
        dest=u'timeline_name', type=unicode, action=u'store',
        default=u'', required=False, help=(
            u'The name of the timeline in Timesketch. Default: '
            u'hostname if present in the storage file. If no hostname '
            u'is found then manual input is used.'))
    argument_group.add_argument(
        u'--index', dest=u'index', type=unicode, action=u'store',
        default=default_uid, required=False, help=(
            u'The name of the Elasticsearch index. Default: Generate a random '
            u'UUID'))
    argument_group.add_argument(
        u'--flush_interval', '--flush-interval', dest=u'flush_interval',
        type=int, action=u'store', default=1000, required=False, help=(
            u'The number of events to queue up before sent in bulk '
            u'to Elasticsearch. Default: 1000'))

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
    if not isinstance(output_module, timesketch_out.TimesketchOutputModule):
      raise errors.BadConfigObject(
          u'Output module is not an instance of TimesketchOutputModule')

    output_format = getattr(options, u'output_format', None)
    if output_format != u'timesketch':
      raise errors.BadConfigOption(u'Only works on Timesketch output module.')

    flush_interval = getattr(options, u'flush_interval', None)
    if flush_interval:
      output_module.SetFlushInterval(flush_interval)

    index = getattr(options, u'index', None)
    if index:
      output_module.SetIndex(index)

    name = getattr(options, u'timeline_name', None)
    if name:
      output_module.SetName(name)


manager.ArgumentHelperManager.RegisterHelper(TimesketchOutputHelper)
