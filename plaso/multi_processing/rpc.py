# -*- coding: utf-8 -*-
"""The RPC client and server interface."""

import abc


def GetProxyPortNumberFromPID(process_id):
  """Determines a port number based on a PID value.

  Args:
    process_id: An integer, process ID (PID), value that should be used to find
                a port number.

  Returns:
    An integer indicating a possible port number for the process to listen on.
  """
  # TODO: Improve this method of selecting ports.
  if process_id > 65535:
    process_id %= 65535

  if process_id < 1024:
    process_id += 1024

  return process_id


class RPCClient(object):
  """Class that defines the RPC client interface."""

  @abc.abstractmethod
  def CallFunction(self):
    """Calls the function via RPC."""

  @abc.abstractmethod
  def Close(self):
    """Closes the RPC communication channel to the server."""

  @abc.abstractmethod
  def Open(self, hostname, port):
    """Opens a RPC communication channel to the server.

    Args:
      hostname: the hostname or IP address to connect to for requests.
      port: the port to connect to for requests.

    Returns:
      A boolean indicating if the communication channel was established.
    """


class RPCServer(object):
  """Class that defines the RPC server interface."""

  def __init__(self, callback):
    """Initializes the RPC server object.

    Args:
      callback: the callback function to invoke on get status RPC request.
    """
    super(RPCServer, self).__init__()
    self._callback = callback

  @abc.abstractmethod
  def Start(self, hostname, port):
    """Starts the RPC server.

    Args:
      hostname: the hostname or IP address to connect to for requests.
      port: the port to connect to for requests.

    Returns:
      A boolean indicating if the RPC server was successfully started.
    """

  @abc.abstractmethod
  def Stop(self):
    """Stops the RPC server."""
