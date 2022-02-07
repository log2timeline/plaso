#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script to plot CPU usage from profiling data.

This script requires the matplotlib and numpy Python modules.
"""

import argparse
import glob
import os
import sys

import numpy

from matplotlib import pyplot


def Main():
  """The main program function.

  Returns:
    bool: True if successful or False if not.
  """
  argument_parser = argparse.ArgumentParser(description=(
      'Plots CPU usage from profiling data.'))

  argument_parser.add_argument(
      '--output', dest='output_file', type=str, help=(
          'path of the output file to write the graph to instead of using '
          'interactive mode. The output format deduced from the extension '
          'of the filename.'))

  argument_parser.add_argument(
      '--process', dest='process', type=str, default='', help=(
          'comma separated list of names of processes to graph.'))

  argument_parser.add_argument(
      '--profiler', dest='profiler', type=str, default='processing', help=(
          'name of the CPU profiler to graph.'))

  argument_parser.add_argument(
      'profile_path', type=str, help=(
          'path to the directory containing the profiling data.'))

  options = argument_parser.parse_args()

  if not os.path.isdir(options.profile_path):
    print('No such directory: {0:s}'.format(options.profile_path))
    return False

  if options.profiler not in ('analyzers', 'parsers', 'processing'):
    print('Unsupported profiler: {0:s}'.format(options.profiler))
    return False

  processes = []
  if options.process:
    processes = options.process.split(',')

  if options.profiler == 'analyzers':
    name_prefix = 'analyzers'
    name_suffix = 'analyzers'

  elif options.profiler == 'parsers':
    name_prefix = 'cputime'
    name_suffix = 'parsers'

  elif options.profiler == 'processing':
    name_prefix = 'processing'
    name_suffix = 'processing'

  names = ['time', 'name', 'cpu']

  glob_pattern = '{0:s}-*-{1:s}.csv.gz'.format(name_prefix, name_suffix)
  glob_expression = os.path.join(options.profile_path, glob_pattern)
  for csv_file_name in glob.glob(glob_expression):
    process_name = os.path.basename(csv_file_name)
    process_name_prefix = '{0:s}-'.format(name_prefix)
    process_name_suffix = '-{0:s}.csv.gz'.format(name_suffix)
    process_name = process_name.replace(process_name_prefix, '').replace(
        process_name_suffix, '')
    if processes and process_name not in processes:
      continue

    data = numpy.genfromtxt(
        csv_file_name, delimiter='\t', dtype=None, encoding='utf-8',
        names=names, skip_header=1)

    if data.size > 0:
      for name in numpy.unique(data['name']):
        # Ignore process_sources since it is a single sample that contains
        # the cumulative CPU time.
        if options.profiler == 'processing' and name == 'process_sources':
          continue

        data_by_name = numpy.extract(data['name'] == name, data)
        label = '-'.join([name, process_name])
        pyplot.plot(data_by_name['time'], data_by_name['cpu'], label=label)

  pyplot.title('CPU usage over time')

  pyplot.xlabel('Time')
  pyplot.xscale('linear')

  pyplot.ylabel('Used CPU')
  pyplot.yscale('linear')

  pyplot.legend()

  if options.output_file:
    pyplot.savefig(options.output_file)
  else:
    pyplot.show()

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
