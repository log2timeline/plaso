# -*- coding: utf-8 -*-
"""The RPC client and server interface."""

import abc


class RPCClient(object):
  """RPC client interface."""

  @abc.abstractmethod
  def CallFunction(self):
    """Calls the function via RPC."""

  @abc.abstractmethod
  def Close(self):
    """Closes the RPC communication channel to the server."""

  # pylint: disable=redundant-returns-doc
  @abc.abstractmethod
  def Open(self, hostname, port):
    """Opens a RPC communication channel to the server.

    Args:
      hostname (str): hostname or IP address to connect to for requests.
      port (int): port to connect to for requests.

    Returns:
      bool: True if the communication channel was established.
    """


class RPCServer(object):
  """RPC server interface."""

  def __init__(self, callback):
    """Initializes the RPC server object.

    Args:
      callback (function): callback to invoke on get status RPC request.
    """
    super(RPCServer, self).__init__()
    self._callback = callback

  # pylint: disable=redundant-returns-doc
  @abc.abstractmethod
  def Start(self, hostname, port):
    """Starts the RPC server.

    Args:
      hostname (str): hostname or IP address to connect to for requests.
      port (int): port to connect to for requests.

    Returns:
      bool: True if the RPC server was successfully started.
    """

  @abc.abstractmethod
  def Stop(self):
    """Stops the RPC server."""
