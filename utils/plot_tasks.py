#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script to plot tasks from profiling data.

This script requires the matplotlib and numpy Python modules.
"""

import argparse
import glob
import os
import sys

import numpy

from matplotlib import pyplot


class TaskMeasurements(object):
  """Measurements of a task.

  Attributes:
    completed_time (float): time when the task was completed by the foreman.
    created_time (float): time when the task was created by the foreman.
    merging_duration (float): time it took the foreman to merge the task.
    merging_time (float): time when the task was started to be merged by
        the foreman.
    pending_merge (float): time when the task was scheduled to be merged by
        the foreman.
    processed_time (float): time when the task was processed according to
        the foreman.
    processing_duration (float): time it took the worker to process the task.
    processing_time (float): time when the task started to be processed by
        the worker.
    scheduled_time (float): time when the task was scheduled onto the task
        queue by the foreman.
  """

  def __init__(self):
    """Initializes a task measurement."""
    super(TaskMeasurements, self).__init__()
    self.completed_time = None
    self.created_time = None
    self.merging_duration = None
    self.merging_time = None
    self.pending_merge_time = None
    self.processed_time = None
    self.processing_duration = None
    self.processing_time = None
    self.scheduled_time = None


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

  names = ['time', 'identifier', 'status']

  measurements = {}

  glob_expression = os.path.join(options.profile_path, 'tasks-*.csv.gz')
  for csv_file_name in glob.glob(glob_expression):
    data = numpy.genfromtxt(
        csv_file_name, delimiter='\t', dtype=None, encoding='utf-8',
        names=names, skip_header=1)

    label = os.path.basename(csv_file_name)
    label = label.replace('tasks-', '').replace('.csv.gz', '')

    for time, identifier, status in data:
      if identifier not in measurements:
        measurements[identifier] = TaskMeasurements()

      task_measurement = measurements[identifier]

      if status == 'completed':
        task_measurement.completed_time = time
        task_measurement.merging_duration = time - task_measurement.merging_time

      elif status == 'created':
        task_measurement.created_time = time

      # TODO: add support for:
      # elif status == 'merge_on_hold':
      # elif status == 'merge_resumed':

      elif status == 'merge_started':
        task_measurement.merging_time = time

      elif status == 'pending_merge':
        task_measurement.pending_merge_time = time

      elif status == 'processed':
        task_measurement.processed_time = time

      elif status == 'processing_started':
        task_measurement.processing_time = time

      elif status == 'processing_completed':
        task_measurement.processing_duration = (
            time - task_measurement.processing_time)

      elif status == 'scheduled':
        task_measurement.scheduled_time = time

  before_pending_merge_duration = {}
  before_queued_duration = {}
  merging_duration = {}
  pending_merge_duration = {}
  processing_duration = {}
  queued_duration = {}

  for identifier, task_measurement in measurements.items():
    before_pending_merge_duration[task_measurement.scheduled_time] = (
        task_measurement.pending_merge_time - (
            task_measurement.processing_time +
            task_measurement.processing_duration))

    before_queued_duration[task_measurement.scheduled_time] = (
        task_measurement.scheduled_time - task_measurement.created_time)

    merging_duration[task_measurement.merging_time] = (
        task_measurement.merging_duration)

    pending_merge_duration[task_measurement.processing_time] = (
        task_measurement.merging_time - task_measurement.pending_merge_time)

    processing_duration[task_measurement.processing_time] = (
        task_measurement.processing_duration)

    queued_duration[task_measurement.scheduled_time] = (
        task_measurement.processing_time - task_measurement.scheduled_time)

  if data.size > 0:
    keys = sorted(before_pending_merge_duration.keys())
    values = [before_pending_merge_duration[key] for key in keys]
    pyplot.plot(keys, values, label='Before pending merge')

    keys = sorted(before_queued_duration.keys())
    values = [before_queued_duration[key] for key in keys]
    pyplot.plot(keys, values, label='Before queued')

    keys = sorted(merging_duration.keys())
    values = [merging_duration[key] for key in keys]
    pyplot.plot(keys, values, label='Merging')

    keys = sorted(pending_merge_duration.keys())
    values = [pending_merge_duration[key] for key in keys]
    pyplot.plot(keys, values, label='Pending merge')

    keys = sorted(processing_duration.keys())
    values = [processing_duration[key] for key in keys]
    pyplot.plot(keys, values, label='Processing')

    keys = sorted(queued_duration.keys())
    values = [queued_duration[key] for key in keys]
    pyplot.plot(keys, values, label='Queued')

  pyplot.title('Task status duration')

  pyplot.xlabel('Time')
  pyplot.xscale('linear')

  pyplot.ylabel('Duration')
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
