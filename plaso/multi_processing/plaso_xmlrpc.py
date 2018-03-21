# -*- coding: utf-8 -*-
"""XML RPC proxy server and client."""

from __future__ import unicode_literals

import logging
import sys
import threading

# pylint: disable=import-error,wrong-import-order
if sys.version_info[0] < 3:
  import xmlrpclib
  import SimpleXMLRPCServer
  import SocketServer
else:
  from xmlrpc import server as SimpleXMLRPCServer
  from xmlrpc import client as xmlrpclib
  import socketserver as SocketServer

# pylint: disable=wrong-import-position
from xml.parsers import expat

from plaso.multi_processing import rpc


class XMLRPCClient(rpc.RPCClient):
  """Class that defines the XML RPC client."""

  _RPC_FUNCTION_NAME = ''

  def __init__(self):
    """Initializes the process status RPC client object."""
    super(XMLRPCClient, self).__init__()
    self._xmlrpc_proxy = None

  def CallFunction(self):
    """Calls the function via RPC."""
    if self._xmlrpc_proxy is None:
      return None

    rpc_call = getattr(self._xmlrpc_proxy, self._RPC_FUNCTION_NAME, None)
    if rpc_call is None:
      return None

    try:
      return rpc_call()
    except (
        expat.ExpatError, SocketServer.socket.error,
        xmlrpclib.Fault) as exception:
      logging.warning('Error while making RPC call: {0:s}'.format(exception))
      return None

  def Close(self):
    """Closes the RPC communication channel to the server."""
    self._xmlrpc_proxy = None

  def Open(self, hostname, port):
    """Opens a RPC communication channel to the server.

    Args:
      hostname: the hostname or IP address to connect to for requests.
      port: the port to connect to for requests.

    Returns:
      A boolean indicating if the communication channel was established.
    """
    server_url = 'http://{0:s}:{1:d}'.format(hostname, port)
    try:
      self._xmlrpc_proxy = xmlrpclib.ServerProxy(server_url, allow_none=True)
    except SocketServer.socket.error as exception:
      logging.warning((
          'Unable to connect to RPC server on {0:s}:{1:d} with error: '
          '{2:s}').format(hostname, port, exception))
      return False

    return True


class ThreadedXMLRPCServer(rpc.RPCServer):
  """Class that defines the threaded XML RPC server."""

  _RPC_FUNCTION_NAME = ''
  _THREAD_NAME = ''

  def __init__(self, callback):
    """Initialize the RPC server.

    Args:
      callback: the callback function to invoke on get status RPC request.
    """
    super(ThreadedXMLRPCServer, self).__init__(callback)
    self._rpc_thread = None
    self._xmlrpc_server = None

  def _Close(self):
    """Closes the RPC communication channel for clients."""
    if not self._xmlrpc_server:
      return
    self._xmlrpc_server.shutdown()
    self._xmlrpc_server = None

  def _Open(self, hostname, port):
    """Opens the RPC communication channel for clients.

    Args:
      hostname: the hostname or IP address to connect to for requests.
      port: the port to connect to for requests.

    Returns:
      A boolean indicating if the communication channel was successfully opened.
    """
    try:
      self._xmlrpc_server = SimpleXMLRPCServer.SimpleXMLRPCServer(
          (hostname, port), logRequests=False, allow_none=True)
    except SocketServer.socket.error as exception:
      logging.warning((
          'Unable to bind a RPC server on {0:s}:{1:d} with error: '
          '{2:s}').format(hostname, port, exception))
      return False

    self._xmlrpc_server.register_function(
        self._callback, self._RPC_FUNCTION_NAME)
    return True

  def Start(self, hostname, port):
    """Starts the process status RPC server.

    Args:
      hostname: the hostname or IP address to connect to for requests.
      port: the port to connect to for requests.

    Returns:
      A boolean indicating if the RPC server was successfully started.
    """
    if not self._Open(hostname, port):
      return False

    self._rpc_thread = threading.Thread(
        name=self._THREAD_NAME, target=self._xmlrpc_server.serve_forever)
    self._rpc_thread.start()
    return True

  def Stop(self):
    """Stops the process status RPC server."""
    self._Close()

    if self._rpc_thread.isAlive():
      self._rpc_thread.join()
    self._rpc_thread = None


class XMLProcessStatusRPCClient(XMLRPCClient):
  """Class that defines a XML process status RPC client."""

  _RPC_FUNCTION_NAME = 'status'


class XMLProcessStatusRPCServer(ThreadedXMLRPCServer):
  """Class that defines a XML process status RPC server."""

  _RPC_FUNCTION_NAME = 'status'
  _THREAD_NAME = 'process_status_rpc_server'
