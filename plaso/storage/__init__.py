# -*- coding: utf-8 -*-
"""This register attribute container storage data types and serializers."""

from acstore.helpers import schema as schema_helper

from plaso.storage import serializers


schema_helper.SchemaHelper.RegisterDataTypes({
    'dfdatetime.DateTimeValues': {
        'json': serializers.JSONDateTimeAttributeSerializer()},
    'dfvfs.PathSpec': {
        'json': serializers.JSONPathSpecAttributeSerializer()},
    'List[str]': {
        'json': serializers.JSONStringsListAttributeSerializer()}})
