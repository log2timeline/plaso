#!/usr/bin/python
# -*- coding: utf-8 -*-
"""The image export front-end."""

import argparse
import logging
import os
import sys

from plaso.frontend import image_export
from plaso.lib import errors


def Main():
  """The main function, running the show."""
  front_end = image_export.ImageExportFrontend()

  arg_parser = argparse.ArgumentParser(
      description=(
          u'This is a simple collector designed to export files inside an '
          u'image, both within a regular RAW image as well as inside a VSS. '
          u'The tool uses a collection filter that uses the same syntax as a '
          u'targeted plaso filter.'),
      epilog=u'And that\'s how you export files, plaso style.')

  arg_parser.add_argument(
      u'-d', u'--debug', dest=u'debug', action=u'store_true', default=False,
      help=u'Turn on debugging information.')

  arg_parser.add_argument(
      u'-w', u'--write', action=u'store', dest=u'path', type=unicode,
      metavar=u'PATH', default=u'export', help=(
          u'The directory in which extracted files should be stored.'))

  arg_parser.add_argument(
      u'-f', u'--filter', action=u'store', dest=u'filter', type=unicode,
      metavar=u'FILTER_FILE', help=(
          u'Full path to the file that contains the collection filter, '
          u'the file can use variables that are defined in preprocesing, '
          u'just like any other log2timeline/plaso collection filter.'))

  arg_parser.add_argument(
      u'--data', action=u'store', dest=u'data_location', type=unicode,
      metavar=u'PATH', default=None, help=u'the location of the data files.')

  arg_parser.add_argument(
      u'--date-filter', u'--date_filter', action=u'append', type=unicode,
      dest=u'date_filters', metavar=u'TYPE_START_END', default=None, help=(
          u'Filter based on file entry date and time ranges. This parameter '
          u'is formatted as "TIME_VALUE,START_DATE_TIME,END_DATE_TIME" where '
          u'TIME_VALUE defines which file entry timestamp the filter applies '
          u'to e.g. atime, ctime, crtime, bkup, etc. START_DATE_TIME and '
          u'END_DATE_TIME define respectively the start and end of the date '
          u'time range. A date time range requires at minimum start or end to '
          u'time of the boundary and END defines the end time. Both timestamps '
          u'be set. The date time values are formatted as: YYYY-MM-DD '
          u'hh:mm:ss.######[+-]##:## Where # are numeric digits ranging from '
          u'0 to 9 and the seconds fraction can be either 3 or 6 digits. The '
          u'time of day, seconds fraction and timezone offset are optional. '
          u'The default timezone is UTC. E.g. "atime, 2013-01-01 23:12:14, '
          u'2013-02-23". This parameter can be repeated as needed to add '
          u'additional date date boundaries, eg: once for atime, once for '
          u'crtime, etc.'))

  arg_parser.add_argument(
      u'-x', u'--extensions', dest=u'extensions_string', action=u'store',
      type=unicode, metavar=u'EXTENSIONS', help=(
          u'Filter based on file name extensions. This option accepts '
          u'multiple multiple comma separated values e.g. "csv,docx,pst".'))

  arg_parser.add_argument(
      u'--names', dest=u'names_string', action=u'store',
      type=str, metavar=u'NAMES', help=(
          u'If the purpose is to find all files given a certain names '
          u'this options should be used. This option accepts a comma separated '
          u'string denoting all file names, eg: -x "NTUSER.DAT,UsrClass.dat".'))

  arg_parser.add_argument(
      u'--signatures', dest=u'signature_identifiers', action=u'store',
      type=unicode, metavar=u'IDENTIFIERS', help=(
          u'Filter based on file format signature identifiers. This option '
          u'accepts multiple comma separated values e.g. "esedb,lnk". '
          u'Use "list" to show an overview of the supported file format '
          u'signatures.'))

  arg_parser.add_argument(
      u'--include_duplicates', dest=u'include_duplicates', action=u'store_true',
      default=False, help=(
          u'By default if VSS is turned on all files saved will have their '
          u'MD5 sum calculated and compared to other files already saved '
          u'with the same inode value. If the MD5 sum is the same the file '
          u'does not get saved again. This option turns off that behavior '
          u'so that all files will get stored, even if they are duplicates.'))

  front_end.AddImageOptions(arg_parser)
  front_end.AddVssProcessingOptions(arg_parser)

  arg_parser.add_argument(
      u'image', nargs='?', action=u'store', metavar=u'IMAGE', default=None,
      type=unicode, help=(
          u'The full path to the image file that we are about to extract files '
          u'from, it should be a raw image or another image that plaso '
          u'supports.'))

  options = arg_parser.parse_args()

  format_str = u'%(asctime)s [%(levelname)s] %(message)s'
  if options.debug:
    logging.basicConfig(level=logging.DEBUG, format=format_str)
  else:
    logging.basicConfig(level=logging.INFO, format=format_str)

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

  if getattr(options, u'signature_identifiers', u'') == u'list':
    front_end.ListSignatureIdentifiers(options)
    return True

  has_filter = False
  if getattr(options, u'date_filters', []):
    has_filter = True
  if getattr(options, u'extensions_string', u''):
    has_filter = True
  if getattr(options, u'filter', u''):
    has_filter = True
  if getattr(options, u'signature_identifiers', u''):
    has_filter = True

  if not has_filter:
    logging.warning(u'No filter defined exporting all files.')

  try:
    front_end.ParseOptions(options, source_option='image')
  except errors.BadConfigOption as exception:
    arg_parser.print_help()
    print u''
    logging.error(u'{0:s}'.format(exception))
    return False

  # TODO: print more status information like PrintOptions.
  front_end.PrintFilterCollection()

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
