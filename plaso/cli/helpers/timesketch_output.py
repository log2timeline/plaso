# -*- coding: utf-8 -*-
"""The Timesketch output module CLI arguments helper."""

import uuid

from plaso.lib import errors
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.output import timesketch_out


class TimesketchOutputArgumentsHelper(interface.ArgumentsHelper):
  """Timesketch output module CLI arguments helper."""

  NAME = u'timesketch'
  CATEGORY = u'output'
  DESCRIPTION = u'Argument helper for the timesketch output module.'

  _DEFAULT_DOC_TYPE = u'plaso_event'
  _DEFAULT_FLUSH_INTERVAL = 1000
  _DEFAULT_NAME = u''
  _DEFAULT_USERNAME = None
  _DEFAULT_UUID = u'{0:s}'.format(uuid.uuid4().hex)

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
        u'--flush_interval', u'--flush-interval', dest=u'flush_interval',
        type=int, action=u'store', default=cls._DEFAULT_FLUSH_INTERVAL,
        required=False, help=(
            u'The number of events to queue up before sent in bulk '
            u'to Elasticsearch.'))

    argument_group.add_argument(
        u'--doc_type', dest=u'doc_type', type=str,
        action=u'store', default=cls._DEFAULT_DOC_TYPE, help=(
            u'Name of the document type that will be used in ElasticSearch.'))

    argument_group.add_argument(
        u'--username', dest=u'username', type=str,
        action=u'store', default=cls._DEFAULT_USERNAME, help=(
            u'Username of a Timesketch user that will own the timeline.'))

  @classmethod
  def ParseOptions(cls, options, output_module):
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options.
      output_module (TimesketchOutputModule): output module to configure.

    Raises:
      BadConfigObject: when the output module object is of the wrong type.
      BadConfigOption: when a configuration parameter fails validation.
    """
    if not isinstance(output_module, timesketch_out.TimesketchOutputModule):
      raise errors.BadConfigObject(
          u'Output module is not an instance of TimesketchOutputModule')

    doc_type = cls._ParseStringOption(
        options, u'doc_time', default_value=cls._DEFAULT_DOC_TYPE)
    output_module.SetDocType(doc_type)

    flush_interval = cls._ParseNumericOption(
        options, u'flush_interval', default_value=cls._DEFAULT_FLUSH_INTERVAL)
    output_module.SetFlushInterval(flush_interval)

    index = cls._ParseStringOption(
        options, u'index', default_value=cls._DEFAULT_UUID)
    output_module.SetIndexName(index)

    name = cls._ParseStringOption(
        options, u'timeline_name', default_value=cls._DEFAULT_NAME)
    output_module.SetTimelineName(name)

    username = cls._ParseStringOption(
        options, u'username', default_value=cls._DEFAULT_USERNAME)
    output_module.SetUserName(username)


manager.ArgumentHelperManager.RegisterHelper(TimesketchOutputArgumentsHelper)
