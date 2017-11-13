import os
import logging

from tinydb import TinyDB, Query, where


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
    """
    [PUT] /admin/{idp}/groups/{groupId}

    Allows to add group mapping to LUMA.

    Args:
        idp (str): Name of IdP (e.g. onedata, github)
        groupId (str): Id of the group in 'idp'
        groupDetails (dict): The mapping between groupId and GID and group name.
    """
    LOG.info('Adding group mapping ({}, {}) -> {}'.format(idp, groupId,
                                                          str(groupDetails)))
    GROUPS.remove((where('idp') == idp) & (where('groupId') == groupId))
    GROUPS.insert({'idp': idp, 'groupId': groupId, 'groupDetails': groupDetails})
    return 'OK', 204


def get_group_mapping(idp, groupId):
    """
    [GET] /admin/{idp}/groups/{groupId}

    Returns group details known by LUMA.

    Args:
        idp (str): Name of IdP (e.g. onedata, github)
        groupId (str): Id of the group in 'idp'
    """
    group = GROUPS.get((where('idp') == idp) & (where('groupId') == groupId))
    if group:
        LOG.info('Returning groupDetails for group {} of {}'.format(groupId,
                                                                    idp))
        return group['groupDetails'], 200
    else:
        LOG.warning('Group {} of idp {} not found'.format(groupId, idp))
        return 'Group not found', 404


def delete_group_mapping(idp, groupId):
    """
    [DELETE] /admin/{idp}/groups/{groupId}

    Allows to remove group mapping from LUMA.

    Args:
        idp (str): Name of IdP (e.g. onedata, github)
        groupId (str): Id of the group in 'idp'
    """
    if GROUPS.remove((where('idp') == idp) & (where('groupId') == groupId)):
        LOG.info('Removed group mapping for group {} of {}'.format(groupId,
                                                                   idp))
        return 'OK', 204
    else:
        LOG.warning('Group {} of idp {} not found'.format(groupId, idp))
        return 'Group not found', 404


def add_user_details(userDetails):
    """
    [POST] /admin/users

    Add user details an return LUMA id.

    Args:
        userDetails (dict): User details which will be used for mapping.
    """
    details = __normalize_user_details(userDetails)
    if details:
        LOG.info('Added userDetails {}'.format(str(userDetails)))
        lid = USERS.insert({'userDetails': details})
        return 'OK', 201, {'Location': '/admin/users/{}'.format(lid)}
    else:
        return ('UserDetails should have at least one '
                'of id or connectedAccounts'), 400


def update_user_details(lid, userDetails):
    """
    [PUT] /admin/users/{lid}

    Allows to update user details, based on which credential mapping will be performed.

    Args:
        lid (str): LUMA user Id.
        userDetails (dict): User details which will be used for mapping.
    """
    details = __normalize_user_details(userDetails)
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
    """
    [GET] /admin/users/{lid}

    Returns user details known by LUMA.

    Args:
        lid (str): LUMA user Id.
    """
    user = USERS.get(eid=lid)
    if user:
        LOG.info('Returning userDetails of /admin/users/{} '.format(lid))
        return user['userDetails'], 200
    else:
        LOG.warning('/admin/users/{} not found'.format(lid))
        return 'User Details not found', 404


def delete_user(lid):
    """
    [DELETE] /admin/users/{lid}

    Deletes user details from LUMA database.

    Args:
        lid (str): LUMA user Id.
    """
    if USERS.remove(eids=[lid]):
        LOG.info('Removed /admin/users/{}'.format(lid))
        return 'OK', 204
    else:
        LOG.warning('/admin/users/{} not found'.format(lid))
        return 'LUMA user not found', 404


def add_user_credentials(lid, credentials):
    """
    [PUT] /admin/users/{lid}/credentials

    Adds user credentials to specific storage.

    Args:
        lid (str): LUMA user Id.
        credentials (dict): User credentials for specific storage.
    """
    if USERS.update({'credentials': credentials}, eids=[lid]):
        LOG.info('Updated credentials for /admin/users/{}'.format(lid))
        return 'OK', 204
    else:
        LOG.warning('/admin/users/{} not found'.format(lid))
        return 'Credentials not found', 404


def map_user_credentials(userCredentialsRequest):
    """
    [POST] /map_user_credentials

    Returns user credentials to storage in JSON format.

    Args:
        userCredentialsRequest (dict): User credentials mapping request.
    """
    LOG.info('map_user_credentials requested for {}'.format(userCredentialsRequest))
    sid = userCredentialsRequest.get('storageId')
    storage_name = userCredentialsRequest.get('storageName')
    user_details = __normalize_user_details(userCredentialsRequest['userDetails'])
    if user_details:
        # Select candidate mappings based on userCredentialRequests
        # First try to match based on Onedata Id
        user = None
        if user_details.get('id') != None:
            user = USERS.get(where('userDetails').id == user_details.get('id'))

        # Next compare IdP specific Id's from "connectedAccounts" list
        if user == None and user_details.get('connectedAccounts'):
            user_accounts = user_details.get('connectedAccounts')
            for account in user_accounts:
                account_query = Query()
                user = USERS.get(where('userDetails').connectedAccounts.any(
                         (account_query.idp == account.get('idp'))
                       & (account_query.userId == account.get('userId'))))
                if user != None:
                    break

        # Next, try to match based on emails, at first top level email
        # from Onedata IdP
        if user == None and user_details.get('emailList'):
            for email in user_details['emailList']:
                user = USERS.get(where('userDetails').emailList.any(email))

        # Finally, try to match based on emails in connectedAccounts
        if user == None and user_details.get('connectedAccounts'):
            user_accounts = user_details.get('connectedAccounts')
            for account in user_accounts:
                if account.get('emailList') == None:
                    continue
                for email in account['emailList']:
                    account_query = Query()
                    user = USERS.get(where('userDetails').connectedAccounts.any(
                              (account_query.idp == account.get('idp'))
                            & (account_query.emailList.any(email))))
                    if user != None:
                        break

        # If we matched some user, check if credentials for requested storage
        # have been provided
        if user and 'credentials' in user:
            for cred in user['credentials']:
                if (cred.get('storageId') != None \
                        and cred.get('storageId') == sid) \
                    or (cred.get('storageName') != None \
                        and cred.get('storageName') == storage_name):
                    LOG.info('Returning credentials for userCredentialsRequest:'
                             '{}'.format(userCredentialsRequest))
                    credentials = {key: val for key, val in cred.items()
                                   if key not in ('aclName', 'storageId', 'storageName', 'type')}
                    return credentials, 200

        LOG.warning('Mapping not found for userCredentialsRequest: '
                    '{}'.format(userCredentialsRequest))
        return 'Mapping not found', 404

    else:
        return ('UserDetails should have at least one '
                'of id or connectedAccounts'), 400


def map_group(groupIdentityRequest):
    """
    [POST] /map_group

    Returns the group identity based on group details.

    Args:
        groupDetailsRequest (dict): Group storage details.
    """
    LOG.info('map_group requested for {}'.format(groupIdentityRequest))
    groupDetails = GROUPS.get(
          (where('idp') == groupIdentityRequest['idp'])
        & (where('groupId') == groupIdentityRequest['groupId']))

    if groupDetails != None and groupDetails.get('groupDetails') != None \
       and len(groupDetails['groupDetails']) > 0:
        LOG.info('map_group returning groupDetails {}'.format(groupDetails['groupDetails'][0]))
        return groupDetails['groupDetails'][0], 200
    else:
        return 'Group details not found', 404


def resolve_user_identity(userStorageCredentials):
    """
    [POST] /resolve_user

    Returns the user identity from storage credentials.

    Args:
        userStorageCredentials (dict): User storage credentials.
    """
    return __resolve_user_identity_base(userStorageCredentials, False)


def resolve_acl_user_identity(userStorageCredentials):
    """
    [POST] /resolve_acl_user

    Returns the user identity based on storage ACL name.

    Args:
        userStorageCredentials (dict): User storage credentials.
    """
    return __resolve_user_identity_base(userStorageCredentials, True)


def __resolve_user_identity_base(userStorageCredentials, acl):

    LOG.info('resolve_user_identity requested for {}'.format(userStorageCredentials))

    # Do not include gid for resolving user identity
    if userStorageCredentials.get('gid'):
        del userStorageCredentials['gid']

    # If this is an ACL resolution request, check if acl user name
    # is provider
    if acl:
        if userStorageCredentials.get('aclName') == None:
            return 'aclName field missing', 404
    else:
        if userStorageCredentials.get('aclName') != None:
            del userStorageCredentials['aclName']

    # Build query using remaining fields from userStorageCredentials
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
        user_details = user['userDetails']
        if user_details.get('id'):
            return {'idp': 'onedata', 'userId': user_details['id']}, 200
        elif len(user_details.get('connectedAccounts')) > 0 \
               and user_details['connectedAccounts'][0].get('userId'):
            return {'idp': user_details['connectedAccounts'][0]['idp'],
                    'userId': user_details['connectedAccounts'][0]['userId']}, 200
        else:
            LOG.warning('Mapping not found for userStorageCredentials: '
                    '{}'.format(userStorageCredentials))
            return 'Mapping not found', 404
    else:
        LOG.warning('Mapping not found for userStorageCredentials: '
                    '{}'.format(userStorageCredentials))
        return 'Mapping not found', 404


def resolve_group(groupStorageDetails):
    """
    [POST] /resolve_group

    Returns group identity based on storage specific group id.

    Args:
        groupDetails (dict): Group mapping request.
    """
    return __resolve_group_base(groupStorageDetails, False)


def resolve_acl_group_identity(groupStorageDetails):
    """
    [POST] /resolve_acl_group

    Returns group identity based on storage specific group ACL name.

    Args:
        groupDetails (dict): Group mapping request.
    """
    return __resolve_group_base(groupStorageDetails, True)


def __resolve_group_base(groupStorageDetails, acl):

    LOG.info('resolve_group requested for {}'.format(groupStorageDetails))
    if groupStorageDetails.get('type') != None:
        del groupDetails['type']

    # If this is an ACL resolution request, check if acl user name
    # is provider
    if acl:
        if groupStorageDetails.get('aclName') == None:
            return 'aclName field missing', 404
    else:
        if groupStorageDetails.get('aclName') != None:
            del groupStorageDetails['aclName']

    conditions = iter(where(attr) == val
                      for attr, val
                      in groupStorageDetails.items())
    query = next(conditions)
    for cond in conditions:
        query &= cond

    group = GROUPS.get(where('groupDetails').any(query))
    if group:
        LOG.info('Returning idp and groupId for groupDetails: '
                 '{}'.format(groupStorageDetails))
        return {'idp': group['idp'], 'groupId': group['groupId']}, 200
    else:
        LOG.warning('Mapping not found for groupDetails: '
                    '{}'.format(groupStorageDetails))
        return 'Mapping not found', 404


def __normalize_user_details(user_details):
    return user_details


