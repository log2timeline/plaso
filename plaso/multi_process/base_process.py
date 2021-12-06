# -*- coding: utf-8 -*-
"""Base class for a process used in multi-processing."""

import abc
import logging
import multiprocessing
import os
import random
import signal
import sys
import time

from plaso.engine import process_info
from plaso.engine import profilers
from plaso.lib import loggers
from plaso.multi_process import logger
from plaso.multi_process import plaso_xmlrpc


class MultiProcessBaseProcess(multiprocessing.Process):
  """Interface for multi-processing process.

  Attributes:
    rpc_port (int): port number of the process status RPC server.
  """

  _NUMBER_OF_RPC_SERVER_START_ATTEMPTS = 14
  _PROCESS_JOIN_TIMEOUT = 5.0

  def __init__(
      self, processing_configuration, enable_sigsegv_handler=False, **kwargs):
    """Initializes a process.

    Args:
      processing_configuration (ProcessingConfiguration): processing
          configuration.
      enable_sigsegv_handler (Optional[bool]): True if the SIGSEGV handler
          should be enabled.
      kwargs (dict[str,object]): keyword arguments to pass to
          multiprocessing.Process.
    """
    super(MultiProcessBaseProcess, self).__init__(**kwargs)
    self._analyzers_profiler = None
    self._debug_output = False
    self._enable_sigsegv_handler = enable_sigsegv_handler
    self._log_filename = None
    self._memory_profiler = None
    self._original_sigsegv_handler = None
    # TODO: check if this can be replaced by self.pid or does this only apply
    # to the parent process?
    self._pid = None
    self._processing_configuration = processing_configuration
    self._process_information = None
    self._processing_profiler = None
    self._quiet_mode = False
    self._rpc_server = None
    self._serializers_profiler = None
    self._status_is_running = False
    self._storage_profiler = None
    self._tasks_profiler = None

    if self._processing_configuration:
      self._debug_output = self._processing_configuration.debug_output

      if processing_configuration.log_filename:
        log_path = os.path.dirname(self._processing_configuration.log_filename)
        log_filename = os.path.basename(
            self._processing_configuration.log_filename)
        log_filename = '{0:s}_{1:s}'.format(self._name, log_filename)
        self._log_filename = os.path.join(log_path, log_filename)

    # We need to share the RPC port number with the engine process.
    self.rpc_port = multiprocessing.Value('I', 0)

  @property
  def name(self):
    """str: process name."""
    return self._name

  # pylint: disable=redundant-returns-doc
  @abc.abstractmethod
  def _GetStatus(self):
    """Returns status information.

    Returns:
      dict [str, object]: status attributes, indexed by name.
    """

  @abc.abstractmethod
  def _Main(self):
    """The process main loop.

    This method is called when the process is ready to start. A sub class
    should override this method to do the necessary actions in the main loop.
    """

  def _OnCriticalError(self):
    """The process on critical error handler.

    This method is called when the process encounters a critical error for
    example a segfault. A sub class should override this method to do the
    necessary actions before the original critical error signal handler it
    called.

    Be aware that the state of the process should not be trusted, as a
    significant part of memory could have been overwritten before a segfault.
    This callback is primarily intended to salvage what we need to troubleshoot
    the error.
    """
    return

  # pylint: disable=unused-argument
  def _SigSegvHandler(self, signal_number, stack_frame):
    """Signal handler for the SIGSEGV signal.

    Args:
      signal_number (int): numeric representation of the signal.
      stack_frame (frame): current stack frame or None.
    """
    self._OnCriticalError()

    # Note that the original SIGSEGV handler can be 0.
    if self._original_sigsegv_handler is not None:
      # Let the original SIGSEGV handler take over.
      signal.signal(signal.SIGSEGV, self._original_sigsegv_handler)
      os.kill(self._pid, signal.SIGSEGV)

  # pylint: disable=unused-argument
  def _SigTermHandler(self, signal_number, stack_frame):
    """Signal handler for the SIGTERM signal.

    Args:
      signal_number (int): numeric representation of the signal.
      stack_frame (frame): current stack frame or None.
    """
    self.SignalAbort()

  def _StartProcessStatusRPCServer(self):
    """Starts the process status RPC server."""
    if self._rpc_server:
      return

    self._rpc_server = plaso_xmlrpc.XMLProcessStatusRPCServer(self._GetStatus)

    hostname = 'localhost'

    # Try the PID as port number first otherwise pick something random
    # between 1024 and 60000.
    if self._pid < 1024 or self._pid > 60000:
      port = random.randint(1024, 60000)
    else:
      port = self._pid

    if not self._rpc_server.Start(hostname, port):
      port = 0
      for _ in range(self._NUMBER_OF_RPC_SERVER_START_ATTEMPTS):
        port = random.randint(1024, 60000)
        if self._rpc_server.Start(hostname, port):
          break

        port = 0

    if not port:
      logger.error((
          'Unable to start a process status RPC server for {0!s} '
          '(PID: {1:d})').format(self._name, self._pid))
      self._rpc_server = None
      return

    self.rpc_port.value = port

    logger.debug(
        'Process: {0!s} process status RPC server started'.format(self._name))

  def _StartProfiling(self, configuration):
    """Starts profiling.

    Args:
      configuration (ProfilingConfiguration): profiling configuration.
    """
    if not configuration:
      return

    if configuration.HaveProfileMemory():
      self._memory_profiler = profilers.MemoryProfiler(
          self._name, configuration)
      self._memory_profiler.Start()

    if configuration.HaveProfileAnalyzers():
      identifier = '{0:s}-analyzers'.format(self._name)
      self._analyzers_profiler = profilers.AnalyzersProfiler(
          identifier, configuration)
      self._analyzers_profiler.Start()

    if configuration.HaveProfileProcessing():
      identifier = '{0:s}-processing'.format(self._name)
      self._processing_profiler = profilers.ProcessingProfiler(
          identifier, configuration)
      self._processing_profiler.Start()

    if configuration.HaveProfileSerializers():
      identifier = '{0:s}-serializers'.format(self._name)
      self._serializers_profiler = profilers.SerializersProfiler(
          identifier, configuration)
      self._serializers_profiler.Start()

    if configuration.HaveProfileStorage():
      self._storage_profiler = profilers.StorageProfiler(
          self._name, configuration)
      self._storage_profiler.Start()

    if configuration.HaveProfileTasks():
      self._tasks_profiler = profilers.TasksProfiler(self._name, configuration)
      self._tasks_profiler.Start()

  def _StopProcessStatusRPCServer(self):
    """Stops the process status RPC server."""
    if not self._rpc_server:
      return

    # Make sure the engine gets one more status update so it knows
    # the worker has completed.
    self._WaitForStatusNotRunning()

    self._rpc_server.Stop()
    self._rpc_server = None
    self.rpc_port.value = 0

    logger.debug(
        'Process: {0!s} process status RPC server stopped'.format(self._name))

  def _StopProfiling(self):
    """Stops profiling."""
    if self._memory_profiler:
      self._memory_profiler.Stop()
      self._memory_profiler = None

    if self._analyzers_profiler:
      self._analyzers_profiler.Stop()
      self._analyzers_profiler = None

    if self._processing_profiler:
      self._processing_profiler.Stop()
      self._processing_profiler = None

    if self._serializers_profiler:
      self._serializers_profiler.Stop()
      self._serializers_profiler = None

    if self._storage_profiler:
      self._storage_profiler.Stop()
      self._storage_profiler = None

    if self._tasks_profiler:
      self._tasks_profiler.Stop()
      self._tasks_profiler = None

  def _WaitForStatusNotRunning(self):
    """Waits for the status is running to change to false."""
    # We wait slightly longer than the status check sleep time.
    time.sleep(2.0)
    time_slept = 2.0
    while self._status_is_running:
      time.sleep(0.5)
      time_slept += 0.5
      if time_slept >= self._PROCESS_JOIN_TIMEOUT:
        break

  # This method is part of the multiprocessing.Process interface hence
  # its name does not follow the style guide.
  def run(self):
    """Runs the process."""
    if '_lsprof' in sys.modules:
      # If profiling is active make sure the worker process is included.
      # cProfile needs to be imported only when needed otherwise the _lsprof
      # module will be loaded.
      import cProfile  # pylint: disable=import-outside-toplevel

      profile = cProfile.Profile()
      profile.enable()
      profile.runcall(self._RunProcess)
      profile.disable()
      profile.dump_stats('{0:s}-profile.output'.format(self._name))
    else:
      self._RunProcess()

  def _RunProcess(self):
    """Runs the process."""
    # Prevent the KeyboardInterrupt being raised inside the process.
    # This will prevent a process from generating a traceback when interrupted.
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    # A SIGTERM signal handler is necessary to make sure IPC is cleaned up
    # correctly on terminate.
    signal.signal(signal.SIGTERM, self._SigTermHandler)

    # A SIGSEGV signal handler is necessary to try to indicate where
    # worker failed.
    # WARNING the SIGSEGV handler will deadlock the process on a real segfault.
    if self._enable_sigsegv_handler:
      self._original_sigsegv_handler = signal.signal(
          signal.SIGSEGV, self._SigSegvHandler)

    self._pid = os.getpid()
    self._process_information = process_info.ProcessInfo(self._pid)

    # We need to set the is running status explicitly to True in case
    # the process completes before the engine is able to determine
    # the status of the process, such as in the unit tests.
    self._status_is_running = True

    # Logging needs to be configured before the first output otherwise we
    # mess up the logging of the parent process.
    loggers.ConfigureLogging(
        debug_output=self._debug_output, filename=self._log_filename,
        quiet_mode=self._quiet_mode)

    logger.debug('Process: {0!s} (PID: {1:d}) started'.format(
        self._name, self._pid))

    self._StartProcessStatusRPCServer()

    logger.debug('Process: {0!s} (PID: {1:d}) enter main'.format(
        self._name, self._pid))

    self._Main()

    logger.debug('Process: {0!s} (PID: {1:d}) exit main'.format(
        self._name, self._pid))

    self._StopProcessStatusRPCServer()

    logger.debug('Process: {0!s} (PID: {1:d}) stopped'.format(
        self._name, self._pid))

    # Make sure log files are cleanly closed.
    logging.shutdown()

    self._status_is_running = False

  @abc.abstractmethod
  def SignalAbort(self):
    """Signals the process to abort."""
