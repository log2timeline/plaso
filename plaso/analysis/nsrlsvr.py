# -*- coding: utf-8 -*-
"""Analysis plugin to look up files in nsrlsvr and tag events."""

from __future__ import unicode_literals

import socket

from plaso.analysis import interface
from plaso.analysis import logger
from plaso.analysis import manager


class NsrlsvrAnalyzer(interface.HashAnalyzer):
  """Analyzes file hashes by consulting an nsrlsvr instance.

  Attributes:
    analyses_performed (int): number of analysis batches completed by this
        analyzer.
    hashes_per_batch (int): maximum number of hashes to analyze at once.
    seconds_spent_analyzing (int): number of seconds this analyzer has spent
        performing analysis (as opposed to waiting on queues, etc.)
    wait_after_analysis (int): number of seconds the analyzer will sleep for
        after analyzing a batch of hashes.
  """
  _RECEIVE_BUFFER_SIZE = 4096
  _SOCKET_TIMEOUT = 3

  SUPPORTED_HASHES = ['md5', 'sha1']

  def __init__(self, hash_queue, hash_analysis_queue, **kwargs):
    """Initializes an nsrlsvr analyzer thread.

    Args:
      hash_queue (Queue.queue): contains hashes to be analyzed.
      hash_analysis_queue (Queue.queue): that the analyzer will append
          HashAnalysis objects this queue.
    """
    super(NsrlsvrAnalyzer, self).__init__(
        hash_queue, hash_analysis_queue, **kwargs)
    self._host = None
    self._port = None
    self.hashes_per_batch = 100

  def _GetSocket(self):
    """Establishes a connection to an nsrlsvr instance.

    Returns:
      socket._socketobject: socket connected to an nsrlsvr instance or None if
          a connection cannot be established.
    """
    try:
      return socket.create_connection(
          (self._host, self._port), self._SOCKET_TIMEOUT)

    except socket.error as exception:
      logger.error(
          'Unable to connect to nsrlsvr with error: {0!s}.'.format(exception))

  def _QueryHash(self, nsrl_socket, digest):
    """Queries nsrlsvr for a specific hash.

    Args:
      nsrl_socket (socket._socketobject): socket of connection to nsrlsvr.
      digest (str): hash to look up.

    Returns:
      bool: True if the hash was found, False if not or None on error.
    """
    try:
      query = 'QUERY {0:s}\n'.format(digest).encode('ascii')
    except UnicodeDecodeError:
      logger.error('Unable to encode digest: {0!s} to ASCII.'.format(digest))
      return False

    response = None

    try:
      nsrl_socket.sendall(query)
      response = nsrl_socket.recv(self._RECEIVE_BUFFER_SIZE)

    except socket.error as exception:
      logger.error('Unable to query nsrlsvr with error: {0!s}.'.format(
          exception))

    if not response:
      return False

    # Strip end-of-line characters since they can differ per platform on which
    # nsrlsvr is running.
    response = response.strip()
    # nsrlsvr returns "OK 1" if the has was found or "OK 0" if not.
    return response == b'OK 1'

  def Analyze(self, hashes):
    """Looks up hashes in nsrlsvr.

    Args:
      hashes (list[str]): hash values to look up.

    Returns:
      list[HashAnalysis]: analysis results, or an empty list on error.
    """
    logger.debug(
        'Opening connection to {0:s}:{1:d}'.format(self._host, self._port))

    nsrl_socket = self._GetSocket()
    if not nsrl_socket:
      self.SignalAbort()
      return []

    hash_analyses = []
    for digest in hashes:
      response = self._QueryHash(nsrl_socket, digest)
      if response is None:
        continue

      hash_analysis = interface.HashAnalysis(digest, response)
      hash_analyses.append(hash_analysis)

    nsrl_socket.close()

    logger.debug(
        'Closed connection to {0:s}:{1:d}'.format(self._host, self._port))

    return hash_analyses

  def SetHost(self, host):
    """Sets the address or hostname of the server running nsrlsvr.

    Args:
      host (str): IP address or hostname to query.
    """
    self._host = host

  def SetPort(self, port):
    """Sets the port where nsrlsvr is listening.

    Args:
      port (int): port to query.
    """
    self._port = port

  def TestConnection(self):
    """Tests the connection to nsrlsvr.

    Checks if a connection can be set up and queries the server for the
    MD5 of an empty file and expects a response. The value of the response
    is not checked.

    Returns:
      bool: True if nsrlsvr instance is reachable.
    """
    response = None
    nsrl_socket = self._GetSocket()
    if nsrl_socket:
      response = self._QueryHash(
          nsrl_socket, 'd41d8cd98f00b204e9800998ecf8427e')
      nsrl_socket.close()

    return response is not None


class NsrlsvrAnalysisPlugin(interface.HashTaggingAnalysisPlugin):
  """Analysis plugin for looking up hashes in nsrlsvr."""

  # The NSRL contains files of all different types, and can handle a high load
  # so look up all files.
  DATA_TYPES = ['fs:stat', 'fs:stat:ntfs']

  URLS = ['https://rjhansen.github.io/nsrlsvr/']

  NAME = 'nsrlsvr'

  def __init__(self):
    """Initializes an nsrlsvr analysis plugin."""
    super(NsrlsvrAnalysisPlugin, self).__init__(NsrlsvrAnalyzer)
    self._label = None

  def GenerateLabels(self, hash_information):
    """Generates a list of strings that will be used in the event tag.

    Args:
      hash_information (bool): whether the analyzer received a response from
          nsrlsvr indicating that the hash was present in its loaded NSRL
          set.

    Returns:
      list[str]: strings describing the results from nsrlsvr.
    """
    if hash_information:
      return [self._label]
    # TODO: Renable when tagging is removed from the analysis report.
    # return ['nsrl_not_present']
    return []

  def SetLabel(self, label):
    """Sets the tagging label.

    Args:
      label (str): label to apply to events extracted from files that are
          present in nsrlsvr.
    """
    self._label = label

  def SetHost(self, host):
    """Sets the address or hostname of the server running nsrlsvr.

    Args:
      host (str): IP address or hostname to query.
    """
    self._analyzer.SetHost(host)

  def SetPort(self, port):
    """Sets the port where nsrlsvr is listening.

    Args:
      port (int): port to query.
    """
    self._analyzer.SetPort(port)

  def TestConnection(self):
    """Tests the connection to nsrlsvr.

    Returns:
      bool: True if nsrlsvr instance is reachable.
    """
    return self._analyzer.TestConnection()


manager.AnalysisPluginManager.RegisterPlugin(NsrlsvrAnalysisPlugin)
