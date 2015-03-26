# -*- coding: utf-8 -*-
"""Simple RPC proxy server and client."""

import SimpleXMLRPCServer
import SocketServer
import xmlrpclib

from xml.parsers import expat

from plaso.lib import errors
from plaso.lib import proxy


class StandardRpcProxyServer(proxy.ProxyServer):
  """Class that implements a simple XML RPC based proxy server."""

  def __init__(self, port=0):
    """Initializes the RPC proxy server object.

    Args:
      port: The port number the proxy should listen on. Defaults to 0.
    """
    super(StandardRpcProxyServer, self).__init__(
        proxy.GetProxyPortNumberFromPID(port))
    self._proxy = None

  def Close(self):
    """Close the proxy object."""
    if not self._proxy:
      return
    self._proxy.shutdown()
    self._proxy = None

  def Open(self):
    """Set up the proxy so that it can be started."""
    try:
      self._proxy = SimpleXMLRPCServer.SimpleXMLRPCServer(
          ('localhost', self.listening_port), logRequests=False,
          allow_none=True)
    except SocketServer.socket.error as exception:
      raise errors.ProxyFailedToStart(
          u'Unable to setup a RPC server for listening to port: {0:d} with '
          u'error: {1:s}'.format(self.listening_port, exception))

  def SetListeningPort(self, new_port_number):
    """Change the port number the proxy listens to.

    Args:
      new_port_number: the new port number.

    Raises:
      RuntimeError: if the proxy is already started.
    """
    if self._proxy:
      raise RuntimeError(
          u'Unable to change proxy port since proxy is already started.')

    self._port_number = proxy.GetProxyPortNumberFromPID(new_port_number)

  def StartProxy(self):
    """Start the proxy."""
    if not self._proxy:
      raise errors.ProxyFailedToStart(u'Proxy not set up yet.')
    self._proxy.serve_forever()

  def RegisterFunction(self, function_name, function):
    """Register a function to this RPC proxy.

    Args:
      function_name: The name of the proxy function.
      function: Callback method to the function providing the requested
                information.
    """
    if not self._proxy:
      raise errors.ProxyFailedToStart((
          u'Unable to register a function for a proxy that has not been set '
          u'up yet.'))
    self._proxy.register_function(function, function_name)


class StandardRpcProxyClient(proxy.ProxyClient):
  """Class that implements a simple XML RPC based proxy client."""

  def __init__(self, port=0):
    """Initializes the RPC proxy client object.

    Args:
      port: The port number the proxy should connect to. Defaults to 0.
    """
    super(StandardRpcProxyClient, self).__init__(
        proxy.GetProxyPortNumberFromPID(port))
    self._proxy = None

  def Open(self):
    """Set up the proxy so that it can be started."""
    try:
      self._proxy = xmlrpclib.ServerProxy(
          u'http://localhost:{0:d}'.format(self._port_number), allow_none=True)
    except SocketServer.socket.error:
      self._proxy = None

  def GetData(self, callback_name):
    """Return back data from the RPC proxy using a callback method.

    Args:
      callback_name: The name of the callback method that the RPC proxy
                     supports.

    Returns:
      The data returned back by the callback method.
    """
    if self._proxy is None:
      return

    callback = getattr(self._proxy, callback_name, None)
    if callback is None:
      return

    try:
      return callback()
    except (SocketServer.socket.error, expat.ExpatError):
      return
