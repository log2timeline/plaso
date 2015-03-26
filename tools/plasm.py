#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This file contains the plasm front-end to plaso."""

import argparse
import logging
import sys
import textwrap

from plaso.frontend import plasm
from plaso.lib import errors


def Main():
  """The main application function."""
  front_end = plasm.PlasmFrontend()

  epilog_tag = ("""
      Notes:

      When applying tags, a tag input file must be given. Currently,
      the format of this file is simply the tag name, followed by
      indented lines indicating conditions for the tag, treating any
      lines beginning with # as comments. For example, a valid tagging
      input file might look like this:'

      ------------------------------
      Obvious Malware
          # anything with 'malware' in the name or path
          filename contains 'malware'

          # anything with the malware datatype
          datatype is 'windows:malware:this_is_not_a_real_datatype'

      File Download
          timestamp_desc is 'File Downloaded'
      ------------------------------

      Tag files can be found in the "extra" directory of plaso.
      """)

  epilog_group = ("""
      When applying groups, the Plaso storage file *must* contain tags,
      as only tagged events are grouped. Plasm can be run such that it
      both applies tags and applies groups, in which case an untagged
      Plaso storage file may be used, since tags will be applied before
      the grouping is calculated.
      """)

  epilog_main = ("""
      For help with a specific action, use "plasm.py {cluster,group,tag} -h".
      """)

  description = (
      u'PLASM (Plaso Langar Ad Safna Minna)- Application to tag and group '
      u'Plaso storage files.')

  arg_parser = argparse.ArgumentParser(
      description=textwrap.dedent(description),
      formatter_class=argparse.RawDescriptionHelpFormatter,
      epilog=textwrap.dedent(epilog_main))

  arg_parser.add_argument(
      '-q', '--quiet', action='store_true', dest='quiet', default=False,
      help='Suppress nonessential output.')

  subparsers = arg_parser.add_subparsers(dest='subcommand')

  cluster_subparser = subparsers.add_parser(
      'cluster', formatter_class=argparse.RawDescriptionHelpFormatter)

  cluster_subparser.add_argument(
      '--closeness', action='store', type=int, metavar='MSEC',
      dest='cluster_closeness', default=5000, help=(
          'Number of miliseconds before we stop considering two '
          'events to be at all "close" to each other'))

  cluster_subparser.add_argument(
      '--threshold', action='store', type=int, metavar='NUMBER',
      dest='cluster_threshold', default=5,
      help='Support threshold for pruning attributes.')

  front_end.AddStorageFileOptions(cluster_subparser)

  group_subparser = subparsers.add_parser(
      'group', formatter_class=argparse.RawDescriptionHelpFormatter,
      epilog=textwrap.dedent(epilog_group))

  front_end.AddStorageFileOptions(group_subparser)

  tag_subparser = subparsers.add_parser(
      'tag', formatter_class=argparse.RawDescriptionHelpFormatter,
      epilog=textwrap.dedent(epilog_tag))

  tag_subparser.add_argument(
      '--tagfile', '--tag_file', '--tag-file', action='store', type=unicode,
      metavar='FILE', dest='tag_filename', help=(
          'Name of the file containing a description of tags and rules '
          'for tagging events.'))

  front_end.AddStorageFileOptions(tag_subparser)

  options = arg_parser.parse_args()

  try:
    front_end.ParseOptions(options)
  except errors.BadConfigOption as exception:
    arg_parser.print_help()
    print u''
    logging.error(u'{0:s}'.format(exception))
    return False

  if front_end.mode == 'cluster':
    front_end.ClusterEvents()

  elif front_end.mode == 'group':
    front_end.GroupEvents()

  elif front_end.mode == 'tag':
    front_end.TagEvents()

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
