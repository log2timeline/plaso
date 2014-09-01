#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2012 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""The log2timeline front-end."""

import argparse
import logging
import multiprocessing
import sys
import time
import textwrap

import plaso
from plaso.frontend import frontend
from plaso.frontend import utils as frontend_utils
from plaso.lib import errors
from plaso.parsers import manager as parsers_manager

import pytz


class LoggingFilter(logging.Filter):
  """Class that implements basic filtering of log events for plaso.

  Some libraries, like binplist, introduce excessive amounts of
  logging that clutters down the debug logs of plaso, making them
  almost non-usable. This class implements a filter designed to make
  the debug logs more clutter-free.
  """

  def filter(self, record):
    """Filter messages sent to the logging infrastructure."""
    if record.module == 'binplist' and record.levelno == logging.DEBUG:
      return False

    return True


class Log2TimelineFrontend(frontend.ExtractionFrontend):
  """Class that implements the log2timeline front-end."""

  _BYTES_IN_A_MIB = 1024 * 1024

  def __init__(self):
    """Initializes the front-end object."""
    input_reader = frontend.StdinFrontendInputReader()
    output_writer = frontend.StdoutFrontendOutputWriter()

    super(Log2TimelineFrontend, self).__init__(input_reader, output_writer)

  def _GetPluginData(self):
    """Return a dict object with a list of all available parsers and plugins."""
    return_dict = {}

    # Import all plugins and parsers to print out the necessary information.
    # This is not import at top since this is only required if this parameter
    # is set, otherwise these libraries get imported in their respected
    # locations.

    # The reason why some of these libraries are imported as '_' is to make sure
    # all appropriate parsers and plugins are registered, yet we don't need to
    # directly call these libraries, it is enough to load them up to get them
    # registered.

    # TODO: remove this hack includes should be a the top if this does not work
    # remove the need for implicit behavior on import.
    from plaso import filters
    from plaso import parsers as _
    from plaso import output as _
    from plaso.frontend import presets
    from plaso.lib import output
    from plaso.parsers import plugins

    return_dict['Versions'] = [
        ('plaso engine', plaso.GetVersion()),
        ('python', sys.version)]

    return_dict['Parsers'] = []
    parsers_list = parsers_manager.ParsersManager.FindAllParsers()
    for parser in sorted(parsers_list['all']):
      doc_string, _, _ = parser.__doc__.partition('\n')
      return_dict['Parsers'].append((parser.parser_name, doc_string))

    return_dict['Parser Lists'] = []
    for category, parsers in sorted(presets.categories.items()):
      return_dict['Parser Lists'].append((category, ', '.join(parsers)))

    return_dict['Output Modules'] = []
    for name, description in sorted(output.ListOutputFormatters()):
      return_dict['Output Modules'].append((name, description))

    return_dict['Plugins'] = []

    for plugin, obj in sorted(plugins.BasePlugin.classes.iteritems()):
      doc_string, _, _ = obj.__doc__.partition('\n')
      return_dict['Plugins'].append((plugin, doc_string))

    return_dict['Filters'] = []
    for filter_obj in sorted(filters.ListFilters()):
      doc_string, _, _ = filter_obj.__doc__.partition('\n')
      return_dict['Filters'].append((filter_obj.filter_name, doc_string))

    return return_dict

  def _GetTimeZones(self):
    """Returns a generator of the names of all the supported time zones."""
    yield 'local'
    for zone in pytz.all_timezones:
      yield zone

  def ListPluginInformation(self):
    """Lists all plugin and parser information."""
    plugin_list = self._GetPluginData()
    return_string_pieces = []

    return_string_pieces.append(
        u'{:=^80}'.format(u' log2timeline/plaso information. '))

    for header, data in plugin_list.items():
      # TODO: Using the frontend utils here instead of "self.PrintHeader"
      # since the desired output here is a string that can be sent later
      # to an output writer. Change this entire function so it can utilize
      # PrintHeader or something similar.
      return_string_pieces.append(frontend_utils.FormatHeader(header))
      for entry_header, entry_data in data:
        return_string_pieces.append(
            frontend_utils.FormatOutputString(entry_header, entry_data))

    return_string_pieces.append(u'')
    self._output_writer.Write(u'\n'.join(return_string_pieces))

  def ListTimeZones(self):
    """Lists the time zones."""
    self._output_writer.Write(u'=' * 40)
    self._output_writer.Write(u'       ZONES')
    self._output_writer.Write(u'-' * 40)
    for timezone in self._GetTimeZones():
      self._output_writer.Write(u'  {0:s}'.format(timezone))
    self._output_writer.Write(u'=' * 40)


def Main():
  """Start the tool."""
  multiprocessing.freeze_support()

  front_end = Log2TimelineFrontend()

  epilog = (
      """
      Example usage:

      Run the tool against an image (full kitchen sink)
          log2timeline.py /cases/mycase/plaso.dump image.dd

      Instead of answering questions, indicate some of the options on the
      command line (including data from particular VSS stores).
          log2timeline.py -o 63 --vss_stores 1,2 /cases/plaso_vss.dump image.E01

      And that's how you build a timeline using log2timeline...
      """)
  description = (
      """
      log2timeline is the main front-end to the plaso back-end, used to
      collect and correlate events extracted from a filesystem.

      More information can be gathered from here:
        http://plaso.kiddaland.net/usage/log2timeline
      """)
  arg_parser = argparse.ArgumentParser(
      description=textwrap.dedent(description),
      formatter_class=argparse.RawDescriptionHelpFormatter,
      epilog=textwrap.dedent(epilog), add_help=False)

  # Create few argument groups to make formatting help messages clearer.
  info_group = arg_parser.add_argument_group('Informational Arguments')
  function_group = arg_parser.add_argument_group('Functional Arguments')
  deep_group = arg_parser.add_argument_group('Deep Analysis Arguments')
  performance_group = arg_parser.add_argument_group('Performance Arguments')

  function_group.add_argument(
      '-z', '--zone', '--timezone', dest='timezone', action='store', type=str,
      default='UTC', help=(
          'Define the timezone of the IMAGE (not the output). This is usually '
          'discovered automatically by preprocessing but might need to be '
          'specifically set if preprocessing does not properly detect or to '
          'overwrite the detected time zone.'))

  function_group.add_argument(
      '-t', '--text', dest='text_prepend', action='store', type=unicode,
      default=u'', metavar='TEXT', help=(
          r'Define a free form text string that is prepended to each path '
          r'to make it easier to distinguish one record from another in a '
          r'timeline (like c:\, or host_w_c:\)'))

  function_group.add_argument(
      '--parsers', dest='parsers', type=str, action='store', default='',
      metavar='PARSER_LIST', help=(
          'Define a list of parsers to use by the tool. This is a comma '
          'separated list where each entry can be either a name of a parser '
          'or a parser list. Each entry can be prepended with a minus sign '
          'to negate the selection (exclude it). The list match is an '
          'exact match while an individual parser matching is a case '
          'insensitive substring match, with support for glob patterns. '
          'Examples would be: "reg" that matches the substring "reg" in '
          'all parser names or the glob pattern "sky[pd]" that would match '
          'all parsers that have the string "skyp" or "skyd" in it\'s name. '
          'All matching is case insensitive.'))

  info_group.add_argument(
      '-h', '--help', action='help', help='Show this help message and exit.')

  info_group.add_argument(
      '--logfile', action='store', metavar='FILENAME', dest='logfile',
      type=unicode, default=u'', help=(
          'If defined all log messages will be redirected to this file instead '
          'the default STDERR.'))

  function_group.add_argument(
      '-p', '--preprocess', dest='preprocess', action='store_true',
      default=False, help=(
          'Turn on preprocessing. Preprocessing is turned on by default '
          'when parsing image files, however if a mount point is being '
          'parsed then this parameter needs to be set manually.'))

  performance_group.add_argument(
      '--buffer_size', '--buffer-size', '--bs', dest='buffer_size',
      action='store', default=0,
      help='The buffer size for the output (defaults to 196MiB).')

  performance_group.add_argument(
      '--workers', dest='workers', action='store', type=int, default=0,
      help=('The number of worker threads [defaults to available system '
            'CPU\'s minus three].'))

  function_group.add_argument(
      '-i', '--image', dest='image', action='store_true', default=False,
      help=(
          'Indicates that this is an image instead of a regular file. It is '
          'not necessary to include this option if -o (offset) is used, then '
          'this option is assumed. Use this when parsing an image with an '
          'offset of zero.'))

  front_end.AddVssProcessingOptions(deep_group)

  performance_group.add_argument(
      '--single_thread', '--single-thread', '--single_process',
      '--single-process', dest='single_process', action='store_true',
      default=False, help=(
          u'Indicate that the tool should run in a single process.'))

  function_group.add_argument(
      '-f', '--file_filter', '--file-filter', dest='file_filter',
      action='store', type=unicode, default=None, help=(
          'List of files to include for targeted collection of files to parse, '
          'one line per file path, setup is /path|file - where each element '
          'can contain either a variable set in the preprocessing stage or a '
          'regular expression'))

  deep_group.add_argument(
      '--scan_archives', dest='open_files', action='store_true', default=False,
      help=argparse.SUPPRESS)

  # This option is "hidden" for the time being, still left in there for testing
  # purposes, but hidden from the tool usage and help messages.
  #    help=('Indicate that the tool should try to open files to extract embedd'
  #          'ed files within them, for instance to extract files from compress'
  #          'ed containers, etc. Be AWARE THAT THIS IS EXTREMELY SLOW.'))

  front_end.AddImageOptions(function_group)

  function_group.add_argument(
      '--partition', dest='partition_number', action='store', type=int,
      default=None, help=(
          'Choose a partition number from a disk image. This partition '
          'number should correspond to the partion number on the disk '
          'image, starting from partition 1.'))

  # Build the version information.
  version_string = u'log2timeline - plaso back-end {0:s}'.format(
      plaso.GetVersion())

  info_group.add_argument(
      '-v', '--version', action='version', version=version_string,
      help='Show the current version of the back-end.')

  info_group.add_argument(
      '--info', dest='show_info', action='store_true', default=False,
      help='Print out information about supported plugins and parsers.')

  info_group.add_argument(
      '--show_memory_usage', '--show-memory-usage', action='store_true',
      default=False, dest='foreman_verbose', help=(
           u'Indicates that basic memory usage should be included in the '
           u'output of the process monitor. If this option is not set the '
           u'tool only displays basic status and counter information.'))

  info_group.add_argument(
      '--disable_worker_monitor', '--disable-worker-monitor',
      action='store_false', default=True, dest='foreman_enabled', help=(
          u'Turn off the foreman. The foreman monitors all worker processes '
          u'and periodically prints out information about all running workers.'
          u'By default the foreman is run, but it can be turned off using this '
          u'parameter.'))

  function_group.add_argument(
      '--use_old_preprocess', '--use-old-preprocess', dest='old_preprocess',
      action='store_true', default=False, help=(
          'Only used in conjunction when appending to a previous storage '
          'file. When this option is used then a new preprocessing object '
          'is not calculated and instead the last one that got added to '
          'the storage file is used. This can be handy when parsing an image '
          'that contains more than a single partition.'))

  function_group.add_argument(
      '--output', dest='output_module', action='store', type=unicode,
      default='', help=(
          'Bypass the storage module directly storing events according to '
          'the output module. This means that the output will not be in the '
          'pstorage format but in the format chosen by the output module. '
          '[Please not this feature is EXPERIMENTAL at this time, use at '
          'own risk (eg. sqlite output does not yet work)]'))

  info_group.add_argument(
      '-d', '--debug', dest='debug', action='store_true', default=False,
      help='Turn on debug information in the tool.')

  arg_parser.add_argument(
      'output', action='store', metavar='STORAGE_FILE', nargs='?',
      type=unicode, help=(
          'The path to the output file, if the file exists it will get '
          'appended to.'))

  arg_parser.add_argument(
      'source', action='store', metavar='SOURCE',
      nargs='?', type=unicode, help=(
          'The path to the source device, file or directory. If the source is '
          'a supported storage media device or image file, archive file or '
          'a directory, the files within are processed recursively.'))

  arg_parser.add_argument(
      'filter', action='store', metavar='FILTER', nargs='?', default=None,
      type=unicode, help=(
          'A filter that can be used to filter the dataset before it '
          'is written into storage. More information about the filters'
          ' and it\'s usage can be found here: http://plaso.kiddaland.'
          'net/usage/filters'))

  # Properly prepare the attributes according to local encoding.
  if front_end.preferred_encoding == 'ascii':
    logging.warning(
        u'The preferred encoding of your system is ASCII, which is not optimal '
        u'for the typically non-ASCII characters that need to be parsed and '
        u'processed. The tool will most likely crash and die, perhaps in a way '
        u'that may not be recoverable. A five second delay is introduced to '
        u'give you time to cancel the runtime and reconfigure your preferred '
        u'encoding, otherwise continue at own risk.')
    time.sleep(5)

  u_argv = [x.decode(front_end.preferred_encoding) for x in sys.argv]
  sys.argv = u_argv
  options = arg_parser.parse_args()

  if options.timezone == 'list':
    front_end.ListTimeZones()
    return True

  if options.show_info:
    front_end.ListPluginInformation()
    return True

  format_str = (
      u'%(asctime)s [%(levelname)s] (%(processName)-10s) PID:%(process)d '
      u'<%(module)s> %(message)s')

  if options.debug:
    if options.logfile:
      logging.basicConfig(
          level=logging.DEBUG, format=format_str, filename=options.logfile)
    else:
      logging.basicConfig(level=logging.DEBUG, format=format_str)

    logging_filter = LoggingFilter()
    root_logger = logging.getLogger()
    root_logger.addFilter(logging_filter)
  elif options.logfile:
    logging.basicConfig(
        level=logging.INFO, format=format_str, filename=options.logfile)
  else:
    logging.basicConfig(level=logging.INFO, format=format_str)

  if not options.output:
    arg_parser.print_help()
    print u''
    arg_parser.print_usage()
    print u''
    logging.error(u'Wrong usage: need to define an output.')
    return False

  try:
    front_end.ParseOptions(options)
    front_end.SetStorageFile(options.output)
  except errors.BadConfigOption as exception:
    arg_parser.print_help()
    print u''
    logging.error(u'{0:s}'.format(exception))
    return False

  # Configure the foreman (monitors workers).
  front_end.SetShowMemoryInformation(show_memory=options.foreman_verbose)
  front_end.SetRunForeman(run_foreman=options.foreman_enabled)

  try:
    front_end.ProcessSource(options)
    logging.info(u'Processing completed.')
  except KeyboardInterrupt:
    logging.warning(u'Aborted by user.')
    front_end.CleanUpAfterAbort()
    return False
  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
