#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Psort (Plaso Síar Og Raðar Þessu) - Makes output from Plaso Storage files.

Sample Usage:
  psort.py /tmp/mystorage.dump "date > '01-06-2012'"

See additional details here: http://plaso.kiddaland.net/usage/psort
"""

import argparse
import multiprocessing
import logging
import pdb
import os
import sys
import time

import plaso

from plaso.frontend import utils as frontend_utils
from plaso.frontend import psort
from plaso.lib import errors


def Main(arguments=None):
  """Start the tool."""
  multiprocessing.freeze_support()

  front_end = psort.PsortFrontend()

  arg_parser = argparse.ArgumentParser(
      description=(
          u'PSORT - Application to read, filter and process '
          u'output from a plaso storage file.'), add_help=False)

  tool_group = arg_parser.add_argument_group(u'Optional arguments For psort')
  output_group = arg_parser.add_argument_group(
      u'Optional arguments for output modules')
  analysis_group = arg_parser.add_argument_group(
      u'Optional arguments for analysis modules')

  tool_group.add_argument(
      u'-d', u'--debug', action=u'store_true', dest=u'debug', default=False,
      help=u'Fall back to debug shell if psort fails.')

  tool_group.add_argument(
      u'-q', u'--quiet', action=u'store_true', dest=u'quiet', default=False,
      help=u'Do not print a summary after processing.')

  tool_group.add_argument(
      u'-h', u'--help', action=u'help',
      help=u'Show this help message and exit.')

  tool_group.add_argument(
      u'-a', u'--include_all', action=u'store_false', dest=u'dedup',
      default=True, help=(
          u'By default the psort removes duplicate entries from the output. '
          u'This parameter changes that behavior so all events are included.'))

  tool_group.add_argument(
      u'-o', u'--output_format', u'--output-format', metavar=u'FORMAT',
      dest=u'output_format', default=u'dynamic', help=(
          u'The output format or "-o list" to see a list of available '
          u'output formats.'))

  tool_group.add_argument(
      u'--analysis', metavar=u'PLUGIN_LIST', dest=u'analysis_plugins',
      default=u'', action=u'store', type=unicode, help=(
          u'A comma separated list of analysis plugin names to be loaded '
          u'or "--analysis list" to see a list of available plugins.'))

  tool_group.add_argument(
      u'--data', metavar=u'PATH', dest=u'data_location', default=u'',
      action=u'store', type=unicode, help=u'The location of the analysis data.')

  tool_group.add_argument(
      u'-z', u'--zone', metavar=u'TIMEZONE', default=u'UTC', dest=u'timezone',
      help=(
          u'The timezone of the output or "-z list" to see a list of available '
          u'timezones.'))

  tool_group.add_argument(
      u'-w', u'--write', metavar=u'OUTPUTFILE', dest=u'write',
      help=u'Output filename, defaults to stdout.')

  tool_group.add_argument(
      u'--slice', metavar=u'DATE', dest=u'slice', type=str,
      default=u'', action=u'store', help=(
          u'Create a time slice around a certain date. This parameter, if '
          u'defined will display all events that happened X minutes before and '
          u'after the defined date. X is controlled by the parameter '
          u'--slice_size but defaults to 5 minutes.'))

  tool_group.add_argument(
      u'--slicer', dest=u'slicer', action=u'store_true', default=False, help=(
          u'Create a time slice around every filter match. This parameter, if '
          u'defined will save all X events before and after a filter match has '
          u'been made. X is defined by the --slice_size parameter.'))

  tool_group.add_argument(
      u'--slice_size', dest=u'slice_size', type=int, default=5, action=u'store',
      help=(
          u'Defines the slice size. In the case of a regular time slice it '
          u'defines the number of minutes the slice size should be. In the '
          u'case of the --slicer it determines the number of events before '
          u'and after a filter match has been made that will be included in '
          u'the result set. The default value is 5]. See --slice or --slicer '
          u'for more details about this option.'))

  tool_group.add_argument(
      u'-v', u'--version', dest=u'version', action=u'version',
      version=u'log2timeline - psort version {0:s}'.format(plaso.GetVersion()),
      help=u'Show the current version of psort.')

  front_end.AddStorageFileOptions(tool_group)

  tool_group.add_argument(
      u'filter', nargs=u'?', action=u'store', metavar=u'FILTER', default=None,
      type=unicode, help=(
          u'A filter that can be used to filter the dataset before it '
          u'is written into storage. More information about the filters'
          u' and it\'s usage can be found here: http://plaso.kiddaland.'
          u'net/usage/filters'))

  if arguments is None:
    arguments = sys.argv[1:]

  # Add the output module options.
  if u'-o' in arguments:
    argument_index = arguments.index(u'-o') + 1
  elif u'--output_format' in arguments:
    argument_index = arguments.index(u'--output_format') + 1
  elif u'--output-format' in arguments:
    argument_index = arguments.index(u'--output-format') + 1
  else:
    argument_index = 0

  if argument_index > 0:
    module_names = arguments[argument_index]
    front_end.AddOutputModuleOptions(output_group, [module_names])

  # Add the analysis plugin options.
  if u'--analysis' in arguments:
    argument_index = arguments.index(u'--analysis') + 1

    # Get the names of the analysis plugins that should be loaded.
    plugin_names = arguments[argument_index]
    try:
      front_end.AddAnalysisPluginOptions(analysis_group, plugin_names)
    except errors.BadConfigOption as exception:
      arg_parser.print_help()
      print u''
      logging.error(u'{0:s}'.format(exception))
      return False

  options = arg_parser.parse_args(args=arguments)

  format_str = u'[%(levelname)s] %(message)s'
  if getattr(options, u'debug', False):
    logging.basicConfig(level=logging.DEBUG, format=format_str)
  else:
    logging.basicConfig(level=logging.INFO, format=format_str)

  if options.timezone == u'list':
    front_end.ListTimeZones()
    return True

  if options.analysis_plugins == u'list':
    front_end.ListAnalysisPlugins()
    return True

  if options.output_format == u'list':
    front_end.ListOutputModules()
    return True

  if not getattr(options, u'data_location', None):
    # Determine if we are running from the source directory.
    options.data_location = os.path.dirname(__file__)
    options.data_location = os.path.dirname(options.data_location)
    options.data_location = os.path.join(options.data_location, u'data')

    if not os.path.exists(options.data_location):
      # Otherwise determine if there is shared plaso data location.
      options.data_location = os.path.join(sys.prefix, u'share', u'plaso')

    if not os.path.exists(options.data_location):
      logging.warning(u'Unable to automatically determine data location.')
      options.data_location = None

  try:
    front_end.ParseOptions(options)
  except errors.BadConfigOption as exception:
    arg_parser.print_help()
    print u''
    logging.error(u'{0:s}'.format(exception))
    return False

  if front_end.preferred_encoding == u'ascii':
    logging.warning(
        u'The preferred encoding of your system is ASCII, which is not optimal '
        u'for the typically non-ASCII characters that need to be parsed and '
        u'processed. The tool will most likely crash and die, perhaps in a way '
        u'that may not be recoverable. A five second delay is introduced to '
        u'give you time to cancel the runtime and reconfigure your preferred '
        u'encoding, otherwise continue at own risk.')
    time.sleep(5)

  try:
    counter = front_end.ProcessStorage(options)

    if not options.quiet:
      logging.info(frontend_utils.FormatHeader(u'Counter'))
      for element, count in counter.most_common():
        logging.info(frontend_utils.FormatOutputString(element, count))

  except IOError as exception:
    # Piping results to "|head" for instance causes an IOError.
    if u'Broken pipe' not in exception:
      logging.error(u'Processing stopped early: {0:s}.'.format(exception))

  except KeyboardInterrupt:
    pass

  # Catching every remaining exception in case we are debugging.
  except Exception as exception:
    if not options.debug:
      raise
    logging.error(u'{0:s}'.format(exception))
    pdb.post_mortem()

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
