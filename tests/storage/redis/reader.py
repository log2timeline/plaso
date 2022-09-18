#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Redis storage file reader."""

import unittest

try:
  # pylint: disable=ungrouped-imports
  import fakeredis
  import redis
  from plaso.storage.redis import reader
except ModuleNotFoundError:
  redis = None

from plaso.containers import sessions
from plaso.containers import tasks

from tests.storage import test_lib


@unittest.skipIf(redis is None, 'missing redis support')
class RedisStorageReaderTest(test_lib.StorageTestCase):
  """Tests for the Redis storage file reader."""

  _REDIS_URL = 'redis://127.0.0.1/0'

  def _CreateRedisClient(self):
    """Creates a Redis client for testing.

    This method will attempt to use a Redis server listening on localhost and
    fallback to a fake Redis client if no server is available or the connection
    timed out.

    Returns:
      Redis: a Redis client.
    """
    try:
      redis_client = redis.from_url(self._REDIS_URL, socket_timeout=60)
      redis_client.ping()
    except redis.exceptions.ConnectionError:
      redis_client = fakeredis.FakeStrictRedis()

    return redis_client

  def testInitialization(self):
    """Tests the __init__ function."""
    test_redis_client = self._CreateRedisClient()

    session = sessions.Session()
    task = tasks.Task(session_identifier=session.identifier)

    test_reader = reader.RedisStorageReader(
        session.identifier, task.identifier, redis_client=test_redis_client)
    self.assertIsNotNone(test_reader)


if __name__ == '__main__':
  unittest.main()
