#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Atlassian Bitbucket access log text parser plugin."""

import unittest

from plaso.parsers.text_plugins import bitbucket_access

from tests.parsers.text_plugins import test_lib


class BitbucketAccessTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for the Atlassian Bitbucket access log text parser plugin."""

  def testParse(self):
    """Tests the Process function."""
    plugin = bitbucket_access.BitbucketAccessTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['atlassian-bitbucket-access.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 6)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # First entry: HTTPS GET with forwarded IP and cache labels.
    expected_event_values = {
        'data_type': 'atlassian:bitbucket:access',
        'http_request_method': 'GET',
        'http_request_uri': '/git/STASH/mina-sshd-fork.git/info/refs',
        'http_request_user_agent': 'git/1.7.4.1',
        'http_response_bytes_read': 13,
        'http_response_bytes_written': 0,
        'http_response_code': 200,
        'http_version': 'HTTP/1.1',
        'labels': 'refs, cache:hit',
        'mesh_execution_id': None,
        'protocol': 'https',
        'recorded_time': '2012-10-29T00:06:26.838',
        'remote_address': '63.246.22.199,172.16.1.187',
        'request_id': 'o@9K7Z3NNx6x3112x1',
        'request_time': 101,
        'session_id': 'tmpqqw',
        'ssh_repository_path': None,
        'user_name': 'eaccru'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    # Second entry: HTTPS POST with referer header.
    expected_event_values = {
        'data_type': 'atlassian:bitbucket:access',
        'http_request_method': 'POST',
        'http_request_uri': (
            '/rest/api/1.0/projects/TEST/repos/test/pull-requests'),
        'http_request_user_agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'),
        'http_response_bytes_read': 832,
        'http_response_bytes_written': 1204,
        'http_response_code': 201,
        'http_version': 'HTTP/1.1',
        'labels': None,
        'mesh_execution_id': None,
        'protocol': 'https',
        'recorded_time': '2022-04-12T05:39:57.408',
        'remote_address': '10.229.31.195',
        'request_id': 'o@2CM38K4Fx339x113x2',
        'request_time': 383,
        'session_id': 'eyoqcd',
        'ssh_repository_path': None,
        'user_name': 'admin'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

    # Third entry: HTTP GET with IPv6 remote address, no user, no session.
    expected_event_values = {
        'data_type': 'atlassian:bitbucket:access',
        'http_request_method': 'GET',
        'http_request_uri': (
            '/rest/api/latest/projects/AAAAA/repos/main/pull-requests/'
            '394/diff'),
        'http_request_user_agent': 'git/2.38.1',
        'http_response_bytes_read': 0,
        'http_response_bytes_written': 9812,
        'http_response_code': 200,
        'http_version': 'HTTP/1.1',
        'labels': None,
        'mesh_execution_id': None,
        'protocol': 'http',
        'recorded_time': '2020-07-21T15:30:52.815',
        'remote_address': '0:0:0:0:0:0:0:1',
        'request_id': 'o@1APC3V1x930x168705816x2',
        'request_time': 47,
        'session_id': None,
        'ssh_repository_path': None,
        'user_name': None}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 2)
    self.CheckEventData(event_data, expected_event_values)

    # Fourth entry: HTTPS POST with access-token labels.
    expected_event_values = {
        'data_type': 'atlassian:bitbucket:access',
        'http_request_method': 'POST',
        'http_request_uri': '/scm/tb/testing-token.git/git-upload-pack',
        'http_request_user_agent': 'git/2.44.0',
        'http_response_bytes_read': 175,
        'http_response_bytes_written': 52,
        'http_response_code': 200,
        'http_version': 'HTTP/1.1',
        'labels': 'access-token:id:263466287238, async, protocol:2, refs',
        'mesh_execution_id': None,
        'protocol': 'https',
        'recorded_time': '2024-05-02T15:52:07.836',
        'remote_address': '10.229.31.195',
        'request_id': 'o@1749XX8x952x97182x0',
        'request_time': 43,
        'session_id': 'eyoqcd',
        'ssh_repository_path': None,
        'user_name': 'testuser'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 3)
    self.CheckEventData(event_data, expected_event_values)

    # Fifth entry: SSH request with repository path.
    expected_event_values = {
        'data_type': 'atlassian:bitbucket:access',
        'http_request_method': 'SSH',
        'http_request_uri': 'git-upload-pack',
        'http_request_user_agent': 'git/2.38.1',
        'http_response_bytes_read': 0,
        'http_response_bytes_written': 9812,
        'http_response_code': 200,
        'http_version': None,
        'labels': 'push',
        'mesh_execution_id': None,
        'protocol': 'ssh',
        'recorded_time': '2020-08-13T10:26:37.907',
        'remote_address': '0:0:0:0:0:0:0:1',
        'request_id': 'o@1APC3V1x930x168705816x2',
        'request_time': 47,
        'session_id': 'abc123',
        'ssh_repository_path': '/stash/stash.git',
        'user_name': 'acarlton'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 4)
    self.CheckEventData(event_data, expected_event_values)

    # Sixth entry: gRPC/Mesh log with mesh_execution_id.
    expected_event_values = {
        'data_type': 'atlassian:bitbucket:access',
        'http_request_method': None,
        'http_request_uri': 'HostingService/HttpBackend',
        'http_request_user_agent': None,
        'http_response_bytes_read': 2,
        'http_response_bytes_written': 141583,
        'http_response_code': 0,
        'http_version': None,
        'labels': None,
        'mesh_execution_id': '@5XDWX5x420x2768x0',
        'protocol': 'grpc',
        'recorded_time': '2022-04-12T07:09:18.086',
        'remote_address': '10.229.31.65',
        'request_id': 'o@1GGG0Q5Kx420x106x2',
        'request_time': None,
        'session_id': None,
        'ssh_repository_path': None,
        'user_name': 'admin'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 5)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
