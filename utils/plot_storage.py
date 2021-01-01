#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script to plot storage IO timing usage from profiling data.

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
      'Plots storage IO timing from profiling data.'))

  argument_parser.add_argument(
      '--output', dest='output_file', type=str, help=(
          'path of the output file to write the graph to instead of using '
          'interactive mode. The output format deduced from the extension '
          'of the filename.'))

  argument_parser.add_argument(
      '--process', dest='process', type=str, default='', help=(
          'comma separated list of names of processes to graph.'))

  argument_parser.add_argument(
      'profile_path', type=str, help=(
          'path to the directory containing the profiling data.'))

  options = argument_parser.parse_args()

  if not os.path.isdir(options.profile_path):
    print('No such directory: {0:s}'.format(options.profile_path))
    return False

  processes = []
  if options.process:
    processes = options.process.split(',')

  names = [
      'time', 'name', 'operation', 'description', 'cpu', 'logical_size', 'size']

  glob_expression = os.path.join(options.profile_path, 'storage-*.csv.gz')
  for csv_file_name in glob.glob(glob_expression):
    process_name = os.path.basename(csv_file_name)
    process_name = process_name.replace('storage-', '').replace('.csv.gz', '')
    if processes and process_name not in processes:
      continue

    data = numpy.genfromtxt(
        csv_file_name, delimiter='\t', dtype=None, encoding='utf-8',
        names=names, skip_header=1)

    if data.size > 0:
      for name in numpy.unique(data['name']):
        data_by_name = numpy.extract(data['name'] == name, data)
        data_bytes_per_second = numpy.divide(
            data_by_name['logical_size'], data_by_name['cpu'])
        label = '-'.join([name, process_name])
        pyplot.plot(data_by_name['time'], data_bytes_per_second, label=label)

  pyplot.title('Bytes read/write over time')

  pyplot.xlabel('Time')
  pyplot.xscale('linear')

  pyplot.ylabel('Bytes per seconds')
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
