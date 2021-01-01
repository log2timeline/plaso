#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script to plot task queue from profiling data.

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
      'Plots memory usage from profiling data.'))

  argument_parser.add_argument(
      '--output', dest='output_file', type=str, help=(
          'path of the output file to write the graph to instead of using '
          'interactive mode. The output format deduced from the extension '
          'of the filename.'))

  argument_parser.add_argument(
      'profile_path', type=str, help=(
          'path to the directory containing the profiling data.'))

  options = argument_parser.parse_args()

  if not os.path.isdir(options.profile_path):
    print('No such directory: {0:s}'.format(options.profile_path))
    return False

  names = ['time', 'queued', 'processing', 'to_merge', 'abandoned', 'total']

  glob_expression = os.path.join(options.profile_path, 'task_queue-*.csv.gz')
  for csv_file_name in glob.glob(glob_expression):
    data = numpy.genfromtxt(
        csv_file_name, delimiter='\t', dtype=None, encoding='utf-8',
        names=names, skip_header=1)

    if data.size > 0:
      pyplot.plot(data['time'], data['queued'], label='queued')
      pyplot.plot(data['time'], data['processing'], label='processing')
      pyplot.plot(data['time'], data['to_merge'], label='to merge')
      pyplot.plot(data['time'], data['abandoned'], label='abandoned')

  pyplot.title('Number of tasks over time')

  pyplot.xlabel('Time')
  pyplot.xscale('linear')

  pyplot.ylabel('Number of tasks')
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
