#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script to plot memory usage from profiling data.

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

  names = ['time', 'name', 'memory']

  glob_expression = os.path.join(options.profile_path, 'memory-*.csv.gz')
  for csv_file_name in glob.glob(glob_expression):
    if csv_file_name.endswith('-parsers.csv.gz'):
      continue

    data = numpy.genfromtxt(
        csv_file_name, delimiter='\t', dtype=None, encoding='utf-8',
        names=names, skip_header=1)

    label = os.path.basename(csv_file_name)
    label = label.replace('memory-', '').replace('.csv.gz', '')

    if data.size > 0:
      pyplot.plot(data['time'], data['memory'], label=label)

  pyplot.title('Memory usage over time')

  pyplot.xlabel('Time')
  pyplot.xscale('linear')

  pyplot.ylabel('Used memory')
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
