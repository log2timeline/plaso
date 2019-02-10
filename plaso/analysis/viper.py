# -*- coding: utf-8 -*-
"""Analysis plugin to look up files in Viper and tag events."""

from __future__ import unicode_literals

from plaso.analysis import interface
from plaso.analysis import logger
from plaso.analysis import manager
from plaso.containers import events
from plaso.lib import errors


class ViperAnalyzer(interface.HTTPHashAnalyzer):
  """Class that analyzes file hashes by consulting Viper.

  REST API reference:
    https://viper-framework.readthedocs.org/en/latest/usage/web.html#api
  """

  SUPPORTED_HASHES = ['md5', 'sha256']
  SUPPORTED_PROTOCOLS = ['http', 'https']

  def __init__(self, hash_queue, hash_analysis_queue, **kwargs):
    """Initializes a Viper hash analyzer.

    Args:
      hash_queue (Queue.queue): contains hashes to be analyzed.
      hash_analysis_queue (Queue.queue): that the analyzer will append
          HashAnalysis objects this queue.
    """
    super(ViperAnalyzer, self).__init__(
        hash_queue, hash_analysis_queue, **kwargs)
    self._checked_for_old_python_version = False
    self._host = None
    self._port = None
    self._protocol = None
    self._url = None

  def _QueryHash(self, digest):
    """Queries the Viper Server for a specfic hash.

    Args:
      digest (str): hash to look up.

    Returns:
      dict[str, object]: JSON response or None on error.
    """
    if not self._url:
      self._url = '{0:s}://{1:s}:{2:d}/file/find'.format(
          self._protocol, self._host, self._port)

    request_data = {self.lookup_hash: digest}

    try:
      json_response = self.MakeRequestAndDecodeJSON(
          self._url, 'POST', data=request_data)

    except errors.ConnectionError as exception:
      json_response = None
      logger.error('Unable to query Viper with error: {0!s}.'.format(
          exception))

    return json_response

  def Analyze(self, hashes):
    """Looks up hashes in Viper using the Viper HTTP API.

    Args:
      hashes (list[str]): hashes to look up.

    Returns:
      list[HashAnalysis]: hash analysis.

    Raises:
      RuntimeError: If no host has been set for Viper.
    """
    hash_analyses = []
    for digest in hashes:
      json_response = self._QueryHash(digest)
      hash_analysis = interface.HashAnalysis(digest, json_response)
      hash_analyses.append(hash_analysis)

    return hash_analyses

  def SetHost(self, host):
    """Sets the address or hostname of the server running Viper server.

    Args:
      host (str): IP address or hostname to query.
    """
    self._host = host

  def SetPort(self, port):
    """Sets the port where Viper server is listening.

    Args:
      port (int): port to query.
    """
    self._port = port

  def SetProtocol(self, protocol):
    """Sets the protocol that will be used to query Viper.

    Args:
      protocol (str): protocol to use to query Viper. Either 'http' or 'https'.

    Raises:
      ValueError: if the protocol is not supported.
    """
    if protocol not in self.SUPPORTED_PROTOCOLS:
      raise ValueError('Unsupported protocol: {0!s}'.format(protocol))

    self._protocol = protocol

  def TestConnection(self):
    """Tests the connection to the Viper server.

    Returns:
      bool: True if the Viper server instance is reachable.
    """
    url = '{0:s}://{1:s}:{2:d}/test'.format(
        self._protocol, self._host, self._port)

    try:
      json_response = self.MakeRequestAndDecodeJSON(url, 'GET')
    except errors.ConnectionError:
      json_response = None

    return json_response is not None


class ViperAnalysisPlugin(interface.HashTaggingAnalysisPlugin):
  """An analysis plugin for looking up SHA256 hashes in Viper."""

  # TODO: Check if there are other file types worth checking Viper for.
  DATA_TYPES = ['pe:compilation:compilation_time']

  URLS = ['https://viper.li']

  NAME = 'viper'

  def __init__(self):
    """Initializes a Viper analysis plugin."""
    super(ViperAnalysisPlugin, self).__init__(ViperAnalyzer)

  def GenerateLabels(self, hash_information):
    """Generates a list of strings that will be used in the event tag.

    Args:
      hash_information (dict[str, object]): JSON decoded contents of the result
          of a Viper lookup, as produced by the ViperAnalyzer.

    Returns:
      list[str]: list of labels to apply to events.
    """
    if not hash_information:
      return ['viper_not_present']

    projects = []
    tags = []
    for project, entries in iter(hash_information.items()):
      if not entries:
        continue

      projects.append(project)

      for entry in entries:
        if entry['tags']:
          tags.extend(entry['tags'])

    if not projects:
      return ['viper_not_present']
    strings = ['viper_present']

    for project_name in projects:
      label = events.EventTag.CopyTextToLabel(
          project_name, prefix='viper_project_')
      strings.append(label)

    for tag_name in tags:
      label = events.EventTag.CopyTextToLabel(tag_name, prefix='viper_tag_')
      strings.append(label)

    return strings

  def SetHost(self, host):
    """Sets the address or hostname of the server running Viper server.

    Args:
      host (str): IP address or hostname to query.
    """
    self._analyzer.SetHost(host)

  def SetPort(self, port):
    """Sets the port where Viper server is listening.

    Args:
      port (int): port to query.
    """
    self._analyzer.SetPort(port)

  def SetProtocol(self, protocol):
    """Sets the protocol that will be used to query Viper.

    Args:
      protocol (str): protocol to use to query Viper. Either 'http' or 'https'.

    Raises:
      ValueError: If an invalid protocol is selected.
    """
    protocol = protocol.lower().strip()
    if protocol not in ['http', 'https']:
      raise ValueError('Invalid protocol specified for Viper lookup')
    self._analyzer.SetProtocol(protocol)

  def TestConnection(self):
    """Tests the connection to the Viper server.

    Returns:
      bool: True if the Viper server instance is reachable.
    """
    return self._analyzer.TestConnection()


manager.AnalysisPluginManager.RegisterPlugin(ViperAnalysisPlugin)
