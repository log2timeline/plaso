#!/usr/bin/python
# -*- coding: utf-8 -*-
"""The log2timeline front-end."""

import argparse
import logging
import multiprocessing
import sys
import time
import textwrap

import plaso

# Registering output modules so that output bypass works.
from plaso import output as _  # pylint: disable=unused-import
from plaso.frontend import frontend
from plaso.frontend import utils as frontend_utils
from plaso.lib import errors
from plaso.hashers import manager as hashers_manager
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
    from plaso import hashers as _  # pylint: disable=redefined-outer-name
    from plaso import parsers as _   # pylint: disable=redefined-outer-name
    from plaso import output as _  # pylint: disable=redefined-outer-name
    from plaso.frontend import presets
    from plaso.output import manager as output_manager

    return_dict[u'Versions'] = [
        (u'plaso engine', plaso.GetVersion()),
        (u'python', sys.version)]

    return_dict[u'Hashers'] = []
    for _, hasher_class in hashers_manager.HashersManager.GetHashers():
      description = getattr(hasher_class, u'DESCRIPTION', u'')
      return_dict[u'Hashers'].append((hasher_class.NAME, description))

    return_dict[u'Parsers'] = []
    for _, parser_class in parsers_manager.ParsersManager.GetParsers():
      description = getattr(parser_class, u'DESCRIPTION', u'')
      return_dict[u'Parsers'].append((parser_class.NAME, description))

    return_dict[u'Parser Lists'] = []
    for category, parsers in sorted(presets.categories.items()):
      return_dict[u'Parser Lists'].append((category, ', '.join(parsers)))

    return_dict[u'Output Modules'] = []
    for name, description in sorted(
        output_manager.OutputManager.GetOutputs()):
      return_dict[u'Output Modules'].append((name, description))

    return_dict[u'Plugins'] = []
    for _, parser_class in parsers_manager.ParsersManager.GetParsers():
      if parser_class.SupportsPlugins():
        for _, plugin_class in parser_class.GetPlugins():
          description = getattr(plugin_class, u'DESCRIPTION', u'')
          return_dict[u'Plugins'].append((plugin_class.NAME, description))

    return_dict[u'Filters'] = []
    for filter_obj in sorted(filters.ListFilters()):
      doc_string, _, _ = filter_obj.__doc__.partition('\n')
      return_dict[u'Filters'].append((filter_obj.filter_name, doc_string))

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
      for entry_header, entry_data in sorted(data):
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

  epilog = u'\n'.join([
      u'',
      u'Example usage:',
      u'',
      u'Run the tool against an image (full kitchen sink)',
      u'    log2timeline.py /cases/mycase/plaso.dump ímynd.dd',
      u'',
      u'Instead of answering questions, indicate some of the options on the',
      u'command line (including data from particular VSS stores).',
      (u'    log2timeline.py -o 63 --vss_stores 1,2 /cases/plaso_vss.dump '
       u'image.E01'),
      u'',
      u'And that\'s how you build a timeline using log2timeline...',
      u''])

  description = u'\n'.join([
      u'',
      u'log2timeline is the main front-end to the plaso back-end, used to',
      u'collect and correlate events extracted from a filesystem.',
      u'',
      u'More information can be gathered from here:',
      u'    http://plaso.kiddaland.net/usage/log2timeline',
      u''])

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
          u'Define the timezone of the IMAGE (not the output). This is usually '
          u'discovered automatically by preprocessing but might need to be '
          u'specifically set if preprocessing does not properly detect or to '
          u'overwrite the detected time zone.'))

  function_group.add_argument(
      '-t', '--text', dest='text_prepend', action='store', type=unicode,
      default=u'', metavar='TEXT', help=(
          u'Define a free form text string that is prepended to each path '
          u'to make it easier to distinguish one record from another in a '
          u'timeline (like c:\\, or host_w_c:\\)'))

  function_group.add_argument(
      '--parsers', dest='parsers', type=str, action='store', default='',
      metavar='PARSER_LIST', help=(
          u'Define a list of parsers to use by the tool. This is a comma '
          u'separated list where each entry can be either a name of a parser '
          u'or a parser list. Each entry can be prepended with a minus sign '
          u'to negate the selection (exclude it). The list match is an '
          u'exact match while an individual parser matching is a case '
          u'insensitive substring match, with support for glob patterns. '
          u'Examples would be: "reg" that matches the substring "reg" in '
          u'all parser names or the glob pattern "sky[pd]" that would match '
          u'all parsers that have the string "skyp" or "skyd" in it\'s name. '
          u'All matching is case insensitive.'))

  function_group.add_argument(
      '--hashers', dest='hashers', type=str, action='store', default='',
      metavar='HASHER_LIST', help=(
          u'Define a list of hashers to use by the tool. This is a comma '
          u'separated list where each entry is the name of a hasher. eg. md5,'
          u'sha256.'
      ))

  info_group.add_argument(
      '-h', '--help', action='help', help=u'Show this help message and exit.')

  info_group.add_argument(
      '--logfile', action='store', metavar='FILENAME', dest='logfile',
      type=unicode, default=u'', help=(
          u'If defined all log messages will be redirected to this file '
          u'instead the default STDERR.'))

  function_group.add_argument(
      '-p', '--preprocess', dest='preprocess', action='store_true',
      default=False, help=(
          u'Turn on preprocessing. Preprocessing is turned on by default '
          u'when parsing image files, however if a mount point is being '
          u'parsed then this parameter needs to be set manually.'))

  front_end.AddPerformanceOptions(performance_group)

  performance_group.add_argument(
      '--workers', dest='workers', action='store', type=int, default=0,
      help=(u'The number of worker threads [defaults to available system '
            u'CPU\'s minus three].'))

  # TODO: seems to be no longer used, remove.
  # function_group.add_argument(
  #     '-i', '--image', dest='image', action='store_true', default=False,
  #     help=(
  #         'Indicates that this is an image instead of a regular file. It is '
  #         'not necessary to include this option if -o (offset) is used, then '
  #         'this option is assumed. Use this when parsing an image with an '
  #         'offset of zero.'))

  front_end.AddVssProcessingOptions(deep_group)

  performance_group.add_argument(
      '--single_thread', '--single-thread', '--single_process',
      '--single-process', dest='single_process', action='store_true',
      default=False, help=(
          u'Indicate that the tool should run in a single process.'))

  function_group.add_argument(
      '-f', '--file_filter', '--file-filter', dest='file_filter',
      action='store', type=unicode, default=None, help=(
          u'List of files to include for targeted collection of files to '
          u'parse, one line per file path, setup is /path|file - where each '
          u'element can contain either a variable set in the preprocessing '
          u'stage or a regular expression.'))

  deep_group.add_argument(
      '--scan_archives', dest='scan_archives', action='store_true',
      default=False, help=argparse.SUPPRESS)

  # This option is "hidden" for the time being, still left in there for testing
  # purposes, but hidden from the tool usage and help messages.
  #    help=('Indicate that the tool should try to open files to extract embedd'
  #          'ed files within them, for instance to extract files from compress'
  #          'ed containers, etc. Be AWARE THAT THIS IS EXTREMELY SLOW.'))

  front_end.AddImageOptions(function_group)

  function_group.add_argument(
      '--partition', dest='partition_number', action='store', type=int,
      default=None, help=(
          u'Choose a partition number from a disk image. This partition '
          u'number should correspond to the partion number on the disk '
          u'image, starting from partition 1.'))

  # Build the version information.
  version_string = u'log2timeline - plaso back-end {0:s}'.format(
      plaso.GetVersion())

  info_group.add_argument(
      '-v', '--version', action='version', version=version_string,
      help=u'Show the current version of the back-end.')

  info_group.add_argument(
      '--info', dest='show_info', action='store_true', default=False,
      help=u'Print out information about supported plugins and parsers.')

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

  front_end.AddExtractionOptions(function_group)

  function_group.add_argument(
      '--output', dest='output_module', action='store', type=unicode,
      default='', help=(
          u'Bypass the storage module directly storing events according to '
          u'the output module. This means that the output will not be in the '
          u'pstorage format but in the format chosen by the output module. '
          u'[Please not this feature is EXPERIMENTAL at this time, use at '
          u'own risk (eg. sqlite output does not yet work)]'))

  function_group.add_argument(
      '--serializer-format', '--serializer_format', dest='serializer_format',
      action='store', default='proto', metavar='FORMAT', help=(
          u'By default the storage uses protobufs for serializing event '
          u'objects. This parameter can be used to change that behavior. '
          u'The choices are "proto" and "json".'))

  front_end.AddInformationalOptions(info_group)

  arg_parser.add_argument(
      'output', action='store', metavar='STORAGE_FILE', nargs='?',
      type=unicode, help=(
          u'The path to the output file, if the file exists it will get '
          u'appended to.'))

  arg_parser.add_argument(
      'source', action='store', metavar='SOURCE',
      nargs='?', type=unicode, help=(
          u'The path to the source device, file or directory. If the source is '
          u'a supported storage media device or image file, archive file or '
          u'a directory, the files within are processed recursively.'))

  arg_parser.add_argument(
      'filter', action='store', metavar='FILTER', nargs='?', default=None,
      type=unicode, help=(
          u'A filter that can be used to filter the dataset before it '
          u'is written into storage. More information about the filters '
          u'and it\'s usage can be found here: http://plaso.kiddaland.'
          u'net/usage/filters'))

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
  try:
    options = arg_parser.parse_args()
  except UnicodeEncodeError:
    # If we get here we are attempting to print help in a "dumb" terminal.
    print arg_parser.format_help().encode(front_end.preferred_encoding)
    return False

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

  except (KeyboardInterrupt, errors.UserAbort):
    logging.warning(u'Aborted by user.')
    return False

  except errors.SourceScannerError as exception:
    logging.warning((
        u'Unable to scan for a supported filesystem with error: {0:s}\n'
        u'Most likely the image format is not supported by the '
        u'tool.').format(exception))
    return False

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
