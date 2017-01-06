#!/usr/bin/env python2
# coding=utf-8
"""Author: Michal Wrona
Copyright (C) 2016 ACK CYFRONET AGH
This software is released under the MIT license cited in 'LICENSE.txt'

Contains request processing logic. Allows to start luma server.
"""

import argparse
import os

from flask import json, request
from luma.app import db, create_app
from luma.config_loader import load_user_credentials_mapping, \
    load_generators_mapping, load_storage_id_to_type_mapping
from luma.model import UserCredentialsMapping, GeneratorsMapping, \
    StorageIdToTypeMapping

from luma.plugins_loader import PluginsLoader

parser = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    description='Start LUMA server')

parser.add_argument(
    '-cm', '--credentials-mapping',
    action='store',
    default=None,
    help='json file with array of credentials mappings',
    dest='credentials_mapping_file')

parser.add_argument(
    '-gm', '--generators-mapping',
    action='store',
    default=None,
    help='json file with array of storages to generators mappings',
    dest='generators_mapping')

parser.add_argument(
    '-sm', '--storages-mapping',
    action='store',
    default=None,
    help='json file with array of storage id to type mappings',
    dest='storages_mapping')

parser.add_argument(
    '-c', '--config',
    action='store',
    default='config.cfg',
    help='cfg file with app configuration',
    dest='config')

args = parser.parse_args()
app = create_app(os.path.join(os.getcwd(), args.config))
plugins = PluginsLoader()


def error_message(code, error_type, message):
    """Creates response with provided code and error JSON response in format:
    {
        "error": "error",
        "errorDescription": "errorDescription"
    }
    """
    response = json.jsonify(error=error_type, errorDescription=message)
    response.status_code = code
    return response


def missing_param(param_name):
    """Creates error response with default message for missing parameter"""
    return error_message(400, 'missing_param',
                         'Missing parameter: {0}'.format(param_name))


@app.route("/map_user_credentials", methods=['POST'])
def map_user_credentials():
    """Handles user credentials mapping request. More detailed
    description in README.
    """
    if app.config['API_KEY'] != request.headers['X-Auth-Token']:
        return error_message(403, 'invalid_token', 'Invalid API token')

    request_data = request.get_json()

    storage_id = request_data.get('storageId')
    storage_type = request_data.get('storageType')
    if not storage_id and not storage_type:
        return missing_param('storageId or storageType')

    space_id = request_data.get('spaceId')
    if not space_id:
        return missing_param('spaceId')

    user_details = request_data.get('userDetails')
    if not user_details:
        return missing_param('userDetails')

    user_id = user_details["id"]

    # If nginx is used as proxy client address is stored under
    # HTTP_X_FORWARDED_FOR. Change this accordingly to your proxy if needed.
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)

    if storage_id and not storage_type:
        id_to_type = StorageIdToTypeMapping.query.filter_by(
            storage_id=storage_id).first()
        if id_to_type:
            storage_type = id_to_type.storage_type

    credentials_mapping = UserCredentialsMapping.query.filter_by(
        user_id=user_id, storage_id=storage_id).first()
    if not credentials_mapping and storage_type:
        credentials_mapping = UserCredentialsMapping.query.filter_by(
            user_id=user_id,
            storage_id=storage_type).first()

    if not credentials_mapping:
        generator_mapping = GeneratorsMapping.query.filter_by(
            storage_id=storage_id).first()
        if not generator_mapping and storage_type:
            generator_mapping = GeneratorsMapping.query.filter_by(
                storage_id=storage_type).first()

        if not generator_mapping:
            return error_message(404, 'unknown_generator',
                                 'Generator not defined for given storageId/Type')
        try:
            generator = plugins.get_plugin(generator_mapping.generator_id)
            credentials = generator.create_user_credentials(storage_type,
                                                            storage_id,
                                                            space_id,
                                                            client_ip,
                                                            user_details)
        except Exception as e:
            return error_message(500, 'internal_server_error', str(e))

        credentials = credentials.to_dict()
        credentials_mapping = UserCredentialsMapping(user_id,
                                                     storage_id or storage_type,
                                                     json.dumps(credentials))
        db.session.add(credentials_mapping)
        db.session.commit()
    else:
        credentials = json.loads(credentials_mapping.credentials)

    return json.jsonify(credentials)


if args.credentials_mapping_file:
    load_user_credentials_mapping(app, args.credentials_mapping_file)
if args.generators_mapping:
    load_generators_mapping(app, plugins, args.generators_mapping)
if args.storages_mapping:
    load_storage_id_to_type_mapping(app, args.storages_mapping)

app.run(host=app.config['HOST'], port=app.config.get('PORT', 5000))
