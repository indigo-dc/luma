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


def add_group_mapping(idp, gid, groupDetails):
    LOG.info('Adding group mapping {} for group {} '
             'of {}'.format(str(groupDetails), gid, idp))
    GROUPS.remove((where('idp') == idp) & (where('gid') == gid))
    GROUPS.insert({'idp': idp, 'gid': gid, 'groupDetails': groupDetails})
    return 'OK', 204


def get_group_mapping(idp, gid):
    group = GROUPS.get((where('idp') == idp) & (where('gid') == gid))
    if group:
        LOG.info('Returning group mapping for group {} of {}'.format(gid, idp))
        return group['groupDetails'], 200
    else:
        LOG.warning('Group {} of idp {} not found'.format(gid, idp))
        return 'Group not found', 404


def delete_group_mapping(idp, gid):
    if GROUPS.remove((where('idp') == idp) & (where('gid') == gid)):
        LOG.info('Removed group mapping for group {} of {}'.format(gid, idp))
        return 'OK', 204
    else:
        LOG.warning('Group {} of idp {} not found'.format(gid, idp))
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
        LOG.info('Returning idp and gid for groupDetails: '
                 '{}'.format(groupDetails))
        return {'idp': group['idp'], 'gid': group['gid']}, 200
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
                'of id or connectedAccounts'), 400


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
                'of id or connectedAccounts'), 400


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
    sid = userCredentialsRequest['storageId']
    user_details = normalize_user_details(userCredentialsRequest['userDetails'])
    if user_details:
        conditions = iter((where('idp') == acc['idp'])
                          & (where('userId') == acc['userId'])
                          for acc in user_details)
        query = next(conditions)
        for cond in conditions:
            query |= cond

        user = USERS.get(where('userDetails').any(query))
        if user:
            for cred in user['credentials']:
                if cred['id'] == sid:
                    LOG.info('Returning credentials for userCredentialsRequest:'
                             '{}'.format(userCredentialsRequest))
                    credentials = {key: val for key, val in cred.items()
                                   if key not in ('id', 'type')}
                    return credentials, 200

        LOG.warning('Mapping not found for userCredentialsRequest: '
                    '{}'.format(userCredentialsRequest))
        return 'Mapping not found', 404

    else:
        return ('UserDetails should have at least one '
                'of id or connectedAccounts'), 400


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
                'userId': user_details['userId']}, 200
    else:
        LOG.warning('Mapping not found for userStorageCredentials: '
                    '{}'.format(userStorageCredentials))
        return 'Mapping not found', 404


def normalize_user_details(user_details):
    try:
        connected_accounts = user_details['connectedAccounts']
    except KeyError:
        connected_accounts = []
    else:
        del user_details['connectedAccounts']

    if 'id' in user_details:
        user_details['idp'] = 'onedata'
        user_details['userId'] = user_details['id']
        del user_details['id']
        connected_accounts.insert(0, user_details)
    elif 'idp' in user_details and 'userId' in user_details:
        connected_accounts.insert(0, user_details)

    return connected_accounts
