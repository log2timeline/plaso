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

  _DEFAULT_FLUSH_INTERVAL = 1000
  _DEFAULT_NAME = u''
  _DEFAULT_UUID = uuid.uuid4().hex

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
        u'--name', u'--timeline_name', u'--timeline-name',
        dest=u'timeline_name', type=str, action=u'store',
        default=cls._DEFAULT_NAME, required=False, help=(
            u'The name of the timeline in Timesketch. Default: '
            u'hostname if present in the storage file. If no hostname '
            u'is found then manual input is used.'))

    argument_group.add_argument(
        u'--index', dest=u'index', type=str, action=u'store',
        default=cls._DEFAULT_UUID, required=False, help=(
            u'The name of the Elasticsearch index. Default: Generate a random '
            u'UUID'))

    argument_group.add_argument(
        u'--flush_interval', '--flush-interval', dest=u'flush_interval',
        type=int, action=u'store', default=cls._DEFAULT_FLUSH_INTERVAL,
        required=False, help=(
            u'The number of events to queue up before sent in bulk '
            u'to Elasticsearch.'))

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

    flush_interval = cls._ParseIntegerOption(
        options, u'flush_interval', default_value=cls._DEFAULT_FLUSH_INTERVAL)
    output_module.SetFlushInterval(flush_interval)

    index = cls._ParseStringOption(
        options, u'index', default_value=cls._DEFAULT_UUID)
    output_module.SetIndex(index)

    name = cls._ParseStringOption(
        options, u'timeline_name', default_value=cls._DEFAULT_NAME)
    output_module.SetName(name)


manager.ArgumentHelperManager.RegisterHelper(TimesketchOutputHelper)
