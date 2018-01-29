import os
import logging

from tinydb import TinyDB, where


LOG_FORMAT = '%(asctime)-15s %(funcName)s %(message)s'
logging.basicConfig(format=LOG_FORMAT)
LOG = logging.getLogger()
LOG.setLevel(logging.INFO)

DB_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                       '..', 'db.json')
DB = TinyDB(DB_PATH)
USERS = DB.table('users')
GROUPS = DB.table('groups')


def add_group_mapping(idp, groupId, groupDetails):
    LOG.info('Adding group mapping ({}, {}) -> {}'.format(idp, groupId,
                                                          str(groupDetails)))
    GROUPS.remove((where('idp') == idp) & (where('groupId') == groupId))
    GROUPS.insert({'idp': idp, 'groupId': groupId, 'groupDetails': groupDetails})
    return 'OK', 204


def get_group_mapping(idp, groupId):
    group = GROUPS.get((where('idp') == idp) & (where('groupId') == groupId))
    if group:
        LOG.info('Returning groupDetails for group {} of {}'.format(groupId,
                                                                    idp))
        return group['groupDetails'], 200
    else:
        LOG.warning('Group {} of idp {} not found'.format(groupId, idp))
        return 'Group not found', 404


def delete_group_mapping(idp, groupId):
    if GROUPS.remove((where('idp') == idp) & (where('groupId') == groupId)):
        LOG.info('Removed group mapping for group {} of {}'.format(groupId,
                                                                   idp))
        return 'OK', 204
    else:
        LOG.warning('Group {} of idp {} not found'.format(groupId, idp))
        return 'Group not found', 404


def resolve_group(groupDetails):
    conditions = iter(where(attr) == val
                      for attr, val
                      in groupDetails.items())
    query = next(conditions)
    for cond in conditions:
        query &= cond

    group = GROUPS.get(where('groupDetails').any(query))
    if group:
        LOG.info('Returning idp and groupId for groupDetails: '
                 '{}'.format(groupDetails))
        return {'idp': group['idp'], 'groupId': group['groupId']}, 200
    else:
        LOG.warning('Mapping not found for groupDetails: '
                    '{}'.format(groupDetails))
        return 'Mapping not found', 404


def post_user_details(userDetails):
    details = normalize_user_details(userDetails)
    if details:
        LOG.info('Added userDetails {}'.format(str(userDetails)))
        lid = USERS.insert({'userDetails': details})
        return 'OK', 201, {'Location': '/admin/users/{}'.format(lid)}
    else:
        return ('UserDetails should have at least one '
                'of id or linkedAccounts'), 400


def update_user_details(lid, userDetails):
    details = normalize_user_details(userDetails)
    if details:
        if USERS.update({'userDetails': details}, eids=[lid]):
            LOG.info('Updated userDetails for /admin/users/{}'.format(lid))
            return 'OK', 204
        else:
            LOG.warning('/admin/users/{} not found'.format(lid))
            return 'User Details not found', 404
    else:
        return ('UserDetails should have at least one '
                'of id or linkedAccounts'), 400


def get_user_details(lid):
    user = USERS.get(eid=lid)
    if user:
        LOG.info('Returning userDetails of /admin/users/{} '.format(lid))
        return user['userDetails'], 200
    else:
        LOG.warning('/admin/users/{} not found'.format(lid))
        return 'User Details not found', 404


def delete_user(lid):
    if USERS.remove(eids=[lid]):
        LOG.info('Removed /admin/users/{}'.format(lid))
        return 'OK', 204
    else:
        LOG.warning('/admin/users/{} not found'.format(lid))
        return 'LUMA user not found', 404


def add_user_credentials(lid, credentials):
    if USERS.update({'credentials': credentials}, eids=[lid]):
        LOG.info('Updated credentials for /admin/users/{}'.format(lid))
        return 'OK', 204
    else:
        LOG.warning('/admin/users/{} not found'.format(lid))
        return 'Credentials not found', 404


def map_user_credentials(userCredentialsRequest):
    sid = userCredentialsRequest.get('storageId')
    storage_name = userCredentialsRequest.get('storageName')
    user_details = normalize_user_details(userCredentialsRequest['userDetails'])
    if user_details:
        conditions = iter((where('idp') == acc['idp'])
                          & (where('subjectId') == acc['subjectId'])
                          for acc in user_details)
        query = next(conditions)
        for cond in conditions:
            query |= cond

        user = USERS.get(where('userDetails').any(query))
        if user and 'credentials' in user:
            for cred in user['credentials']:
                if (cred.get('storageId') != None and cred.get('storageId') == sid) \
                  or (cred.get('storageName') != None and cred.get('storageName') == storage_name):
                    LOG.info('Returning credentials for userCredentialsRequest:'
                             '{}'.format(userCredentialsRequest))
                    credentials = {key: val for key, val in cred.items()
                                   if key not in ('storageId', 'storageName', 'type')}
                    return credentials, 200

        LOG.warning('Mapping not found for userCredentialsRequest: '
                    '{}'.format(userCredentialsRequest))
        return 'Mapping not found', 404

    else:
        return ('UserDetails should have at least one '
                'of id or linkedAccounts'), 400


def resolve_user_identity(userStorageCredentials):
    conditions = iter(where(attr) == val
                      for attr, val
                      in userStorageCredentials.items())
    query = next(conditions)
    for cond in conditions:
        query &= cond

    user = USERS.get(where('credentials').any(query))
    if user:
        LOG.info('Returning idp and gid for userStorageCredentials: '
                 '{}'.format(userStorageCredentials))
        user_details = user['userDetails'][0]
        return {'idp': user_details['idp'],
                'subjectId': user_details['subjectId']}, 200
    else:
        LOG.warning('Mapping not found for userStorageCredentials: '
                    '{}'.format(userStorageCredentials))
        return 'Mapping not found', 404


def normalize_user_details(user_details):
    try:
        linked_accounts = user_details['linkedAccounts']
    except KeyError:
        linked_accounts = []
    else:
        del user_details['linkedAccounts']

    if 'id' in user_details:
        user_details['idp'] = 'onedata'
        user_details['subjectId'] = user_details['id']
        del user_details['id']
        linked_accounts.insert(0, user_details)
    elif 'idp' in user_details and 'subjectId' in user_details:
        linked_accounts.insert(0, user_details)

    return linked_accounts
