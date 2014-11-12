#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
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
"""A simple tool that provides an overview of running log2timeline processes.

The tool iterates over all process running on the system looking for one
running log2timeline. If it finds it, it will print out information detected
from each process.

There is also an option to drop into an IPython shell to further interact with
the process, giving the user the option to for instance terminate processes
that are in a zombie state.
"""

import argparse
import IPython
import sys
import textwrap

import psutil

from plaso.frontend import frontend
from plaso.multi_processing import process_info


def IsWorkerProcess(process):
  """Checks whether a process is a worker process.

  Args:
    process: A process object (instance of ProcessInfo).

  Returns:
    A boolean value indicating whether or not the process is a worker.
  """
  # The parent needs to be log2timeline.
  if not 'log2timeline' in process.parent.name:
    return False

  # If it has an active RPC server then we know for sure.
  rpc_status = process.GetProcessStatus()
  if rpc_status:
    return True

  # We still want to continue checking, in case the RPC
  # server was not working.
  # TODO: Add additional tests to verify this is a worker,
  # perhaps look at libraries loaded, etc.
  return False


class ProcessInformationFrontend(frontend.Frontend):
  """A frontend implementation for the process information tool."""

  def __init__(self):
    """Initialize the process information frontend."""
    self._input_reader = frontend.StdinFrontendInputReader()
    self._output_writer = frontend.StdoutFrontendOutputWriter()
    self._parent_list = []
    self._process_list = []

    super(ProcessInformationFrontend, self).__init__(
        self._input_reader, self._output_writer)

  def PrintRPCDetails(self, process):
    """Print detailed information about a running process.

    Args:
      process: A process object (instance of ProcessInfo).
    """
    self._output_writer.Write(u'RPC Status:\n')
    rpc_status = process.GetProcessStatus()
    if rpc_status:
      for key, value in rpc_status.iteritems():
        self._output_writer.Write(u'\t{0:s} = {1!s}\n'.format(key, value))
    else:
      self._output_writer.Write(u'\tNo RPC client listening.\n')

  def PrintProcessDetails(self, process):
    """Print detailed information about a running process.

    Args:
      process: A process object (instance of ProcessInfo).
    """
    mem_info = process.GetMemoryInformation()

    self.PrintSeparatorLine()
    self._output_writer.Write(u'\n{0:20s}{1:s} [{2:d}]\n'.format(
        u'', process.name, process.pid))
    self.PrintSeparatorLine()
    self.PrintHeader(u'Basic Information')
    self._output_writer.Write(u'Name:\n\t{0:s}\n'.format(process.name))
    self._output_writer.Write(u'PID:\n\t{0:d}\n'.format(process.pid))
    self._output_writer.Write(u'Command Line:\n\t{0:s}\n'.format(
        process.command_line))
    self._output_writer.Write(u'Process Alive:\n\t{0!s}\n'.format(
        process.IsAlive()))
    self._output_writer.Write(u'Process Status:\n\t{0:s}\n'.format(
        process.status))

    is_a_worker = IsWorkerProcess(process)
    if is_a_worker:
      self._output_writer.Write(u'This is a worker thread.\n')
    else:
      self._output_writer.Write(u'This is NOT a worker.\n')

    self._output_writer.Write(u'\n')
    self.PrintHeader(u' * Additional Information')
    self._output_writer.Write(u'Parent PID:\n\t{0:d} ({1:s})\n'.format(
        process.parent.pid, process.parent.name))
    self._output_writer.Write(u'Children:\n')
    for child in process.children:
      self._output_writer.Write(u'\t{0:d} [{1:s}]\n'.format(
          child.pid, child.name))

    if is_a_worker:
      self.PrintRPCDetails(process)

    self._output_writer.Write('Nr. of Threads:\n\t{0:d}\n'.format(
        process.number_of_threads))

    self._output_writer.Write('Open files:\n')
    for open_file in process.open_files:
      self._output_writer.Write(u'\t{0:s}\n'.format(open_file))

    self._output_writer.Write(u'Memory:\n')
    # We need to access a protected attribute to get the
    # name of all the fields in the memory object.
    # pylint: disable=protected-access
    for field in mem_info._fields:
      self._output_writer.Write(u'\t{0:s} = {1!s}\n'.format(
          field, getattr(mem_info, field, u'')))

    self._output_writer.Write('Memory map: \n')
    for memory_map in process.memory_map:
      self._output_writer.Write(u'\t{0:s}\n'.format(memory_map.path))

  def BuildProcessList(self):
    """Build a list of processes."""
    for process_object in psutil.get_process_list():
      # TODO: This may catch other processes, such as "vim
      # foo/log2timeline/foo.py" since that's in the command line. However the
      # python log2timeline.py will cause the older approach of name to fail.
      try:
        command_line = u' '.join(process_object.cmdline)
      # pylint: disable=protected-access
      except psutil._error.AccessDenied:
        continue
      if 'log2timeline' in command_line:
        process_details = process_info.ProcessInfo(pid=process_object.pid)
        self._process_list.append(process_details)
        parent_process = process_details.parent
        children = list(process_details.children)
        if 'log2timeline' not in parent_process.name and len(children):
          self._parent_list.append(process_details)

  def TerminateWorkers(self):
    for process_object in self._process_list:
      # Find out which process is a worker and which one isn't.
      if IsWorkerProcess(process_object):
        self._output_writer.Write(
            u'Killing process: {0:s} [{1:d}] - {2:s}\n'.format(
                process_object.name, process_object.pid,
                process_object.status))
        process_object.TerminateProcess()

  def ListProcesses(self):
    if self._parent_list:
      self._output_writer.Write(u'Main process (careful before killing):\n')
      for parent_process in self._parent_list:
        if parent_process.IsAlive():
          status = u'Alive'
        else:
          status = u'Dead'

        self._output_writer.Write((
            u'{4}\n\tPid: {1:d}\n\tCommand Line: {0:s}\n\tStatus:{2} '
            u'<{3:s}>\n{4:s}\n').format(
                parent_process.command_line, parent_process.pid,
                status, parent_process.status, u'-'*40))
      self._output_writer.Write(u'\n')

    if not self._process_list:
      self._output_writer.Write(
          u'No processes discovered. Are you sure log2timeline is running?\n')
      return

    self._output_writer.Write(u'='*80)
    self._output_writer.Write(u'\n\t\tDiscovered Processes\n')
    self._output_writer.Write(u'='*80)
    self._output_writer.Write(u'\n')
    for process_object in self._process_list:
      self.PrintProcessDetails(process_object)


def Main():
  """Read parameters and run the tool."""
  front_end = ProcessInformationFrontend()

  description = (
      u'A simple tool that tries to list up all processes that belong to '
      u'log2timeline. Once a process is detected it will print out '
      u'statistical information about it, as well as providing an option '
      u'to attempt to "kill" worker threads.')
  arg_parser = argparse.ArgumentParser(
      description=textwrap.dedent(description))

  arg_parser.add_argument(
      '-c', '--console', dest='console', action='store_true', default=False,
      help=u'Open up an IPython console.')

  arg_parser.add_argument(
      '-k', '--kill-workers', '--kill_workers', dest='kill_workers',
      action='store_true', default=False, help=(
          u'The tool does a rudimentary check to discover worker threads '
          u'and terminates those it finds. This can be used in the case '
          u'where the tool is stuck due to a non-functioning worker that '
          u'prevents the tool from completing it\'s processing.'))

  # TODO: Add an option to specify certain parent if we are killing workers.
  options = arg_parser.parse_args()

  front_end.BuildProcessList()

  if options.console:
    IPython.embed()
    return True

  if options.kill_workers:
    front_end.TerminateWorkers()
  else:
    front_end.ListProcesses()

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
