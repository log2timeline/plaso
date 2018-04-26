#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=invalid-name
"""Script to plot memory usage from profiling data.

This script requires the matplotlib and numpy Python modules.
"""

from __future__ import print_function
# mathplotlib does not support Unicode strings a column names.
# from __future__ import unicode_literals

import argparse
import glob
import gzip
import os
import sys

from matplotlib import pyplot  # pylint: disable=import-error
from numpy import genfromtxt  # pylint: disable=import-error


def Main():
  """The main program function.

  Returns:
    bool: True if successful or False if not.
  """
  argument_parser = argparse.ArgumentParser(description=(
      'Plots memory usage from profiling data.'))

  argument_parser.add_argument(
      '--output', dest='output_file', default=str, help=(
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
  types = ['float', 'str', 'float']

  glob_expression = os.path.join(options.profile_path, 'memory-*.csv.gz')
  for csv_file in glob.glob(glob_expression):
    with gzip.open(csv_file, 'rb') as file_object:
      data = genfromtxt(
          file_object, delimiter='\t', dtype=types, names=names, skip_header=1)

    label = os.path.basename(csv_file)
    label = label.replace('memory-', '').replace('.csv.gz', '')
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
