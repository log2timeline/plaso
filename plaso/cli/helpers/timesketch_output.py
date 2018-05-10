# -*- coding: utf-8 -*-
"""The Timesketch output module CLI arguments helper."""

from __future__ import unicode_literals

import uuid

from plaso.lib import errors
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.output import timesketch_out


class TimesketchOutputArgumentsHelper(interface.ArgumentsHelper):
  """Timesketch output module CLI arguments helper."""

  NAME = 'timesketch'
  CATEGORY = 'output'
  DESCRIPTION = 'Argument helper for the timesketch output module.'

  _DEFAULT_DOCUMENT_TYPE = 'plaso_event'
  _DEFAULT_FLUSH_INTERVAL = 1000
  _DEFAULT_NAME = ''
  _DEFAULT_USERNAME = None
  _DEFAULT_UUID = '{0:s}'.format(uuid.uuid4().hex)

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
        '--name', '--timeline_name', '--timeline-name',
        dest='timeline_name', type=str, action='store',
        default=cls._DEFAULT_NAME, required=False, help=(
            'The name of the timeline in Timesketch. Default: '
            'hostname if present in the storage file. If no hostname '
            'is found then manual input is used.'))

    argument_group.add_argument(
        '--index', dest='index', type=str, action='store',
        default=cls._DEFAULT_UUID, required=False, help=(
            'The name of the Elasticsearch index. Default: Generate a random '
            'UUID'))

    argument_group.add_argument(
        '--flush_interval', '--flush-interval', dest='flush_interval',
        type=int, action='store', default=cls._DEFAULT_FLUSH_INTERVAL,
        required=False, help=(
            'The number of events to queue up before sent in bulk '
            'to Elasticsearch.'))

    argument_group.add_argument(
        '--doc_type', dest='document_type', type=str,
        action='store', default=cls._DEFAULT_DOCUMENT_TYPE, help=(
            'Name of the document type that will be used in ElasticSearch.'))

    argument_group.add_argument(
        '--username', dest='username', type=str,
        action='store', default=cls._DEFAULT_USERNAME, help=(
            'Username of a Timesketch user that will own the timeline.'))

  # pylint: disable=arguments-differ
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
          'Output module is not an instance of TimesketchOutputModule')

    document_type = cls._ParseStringOption(
        options, 'document_type', default_value=cls._DEFAULT_DOCUMENT_TYPE)
    output_module.SetDocumentType(document_type)

    flush_interval = cls._ParseNumericOption(
        options, 'flush_interval', default_value=cls._DEFAULT_FLUSH_INTERVAL)
    output_module.SetFlushInterval(flush_interval)

    index = cls._ParseStringOption(
        options, 'index', default_value=cls._DEFAULT_UUID)
    output_module.SetIndexName(index)

    name = cls._ParseStringOption(
        options, 'timeline_name', default_value=cls._DEFAULT_NAME)
    output_module.SetTimelineName(name)

    username = cls._ParseStringOption(
        options, 'username', default_value=cls._DEFAULT_USERNAME)
    output_module.SetTimelineOwner(username)


manager.ArgumentHelperManager.RegisterHelper(TimesketchOutputArgumentsHelper)
