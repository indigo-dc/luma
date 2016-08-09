# coding=utf-8
"""Author: Michal Wrona
Copyright (C) 2016 ACK CYFRONET AGH
This software is released under the MIT license cited in 'LICENSE.txt'

Helper functions to load config from files.
"""

from flask import json
from app import db
from model import StorageIdToTypeMapping, GeneratorsMapping, \
    UserCredentialsMapping


def load_storage_id_to_type_mapping(app, storage_id_to_type_file):
    """Loads storage id to type mapping from file into database"""
    with app.app_context():
        with open(storage_id_to_type_file) as data_file:
            data = json.load(data_file)

            if not isinstance(data, list):
                raise RuntimeError(
                    'Invalid file format, should contain list of id to type mapping')

            for entry in data:
                mapping = StorageIdToTypeMapping(entry['storageId'],
                                                 entry['storageType'])
                db.session.merge(mapping)
            db.session.commit()


def load_generators_mapping(app, plugins, generators_file):
    """Loads generators mapping from file into database"""
    with app.app_context():
        with open(generators_file) as data_file:
            data = json.load(data_file)
            if not isinstance(data, list):
                raise RuntimeError(
                    'Invalid file format, should contain list of generators mapping')

            for entry in data:
                if 'storageId' in entry:
                    storage_id = entry['storageId']
                elif 'storageType' in entry:
                    storage_id = entry['storageType']
                else:
                    raise RuntimeError(
                        'Generators mapping must contain storageId or storageType')

                if entry['generatorId'] not in plugins.get_available_plugins():
                    raise RuntimeError('Generator {} does not exists'.format(
                        entry['generatorId']))
                mapping = GeneratorsMapping(storage_id, entry['generatorId'])
                db.session.merge(mapping)
            db.session.commit()


def load_user_credentials_mapping(app, user_credentials_file):
    """Loads user credentials mapping from file into database"""
    with app.app_context():
        with open(user_credentials_file) as data_file:
            data = json.load(data_file)

            if not isinstance(data, list):
                raise RuntimeError(
                    'Invalid file format, should contain list of credentials')

            for entry in data:
                mapping = UserCredentialsMapping(entry['userId'],
                                                 entry['storageId'],
                                                 json.dumps(
                                                     entry['credentials']))
                db.session.merge(mapping)
            db.session.commit()
