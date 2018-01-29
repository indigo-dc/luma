import time
import random
import string
import unittest
import subprocess as sp

import requests


LUMA_IP = 'localhost'
LUMA_PORT = 8080
LUMA_API_PATH = 'api/v3/luma'
URL = 'http://{ip}:{port}/{api_path}'.format(ip=LUMA_IP, port=LUMA_PORT,
                                             api_path=LUMA_API_PATH)


USER_DETAILS_1 = {
    "id": "9743a66f914cc249efca164485a19c5c"
}

USER_DETAILS_2 = {
  "emailList": [
    "user.1@example2.com",
    "user.one@example2.com",
    "user.i@example2.com"
  ],
  "id": "9743a66f914cc249efca164485a19c5c",
  "linkedAccounts": [
    {
      "emailList": [
        "user.1@example.com",
        "user.one@example.com",
        "user.i@example.com"
      ],
      "idp": "github",
      "login": "user1",
      "name": "User One",
      "subjectId": "5c28904a-124a-4035-853c-36938143dd4e"
    },
    {
      "custom": {
        "eduPersonPrincipalName": "john@example.com",
        "userCertificateSubject": "/C=PL/O=GRID/O=ACME/CN=John Doe"
      },
      "emailList": [
        "user.1@example.com"
      ],
      "idp": "EGI",
      "login": "user1",
      "name": "User One",
      "subjectId": "john@example.com"
    }
  ],
  "login": "user.one",
  "name": "user1"
}

POSIX_STORAGE_CREDENTIALS = {
    "storageId": "1",
    "type": "posix",
    "uid": 1001,
    "gid": 1001
}

S3_STORAGE_CREDENTIALS = {
    "storageId": "2",
    "type": "s3",
    "accessKey": "ABCD",
    "secretKey": "1234"
}

CEPH_STORAGE_CREDENTIALS = {
    "storageId": "3",
    "type": "ceph",
    "key": "ABCD",
    "username": "user1"
}

GLUSTERFS_STORAGE_CREDENTIALS = {
    "storageName": "GlusterFS4",
    "storageId": "4",
    "type": "glusterfs",
    "uid": 1001,
    "gid": 1001
}

MULTI_STORAGE_CREDENTIALS = [
    POSIX_STORAGE_CREDENTIALS,
    S3_STORAGE_CREDENTIALS,
    CEPH_STORAGE_CREDENTIALS,
    GLUSTERFS_STORAGE_CREDENTIALS
]

GROUP_DETAILS = {
    "gid": "1001",
    "name": "users",
    "id": "1"
}


class TestLUMA(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.proc = sp.Popen(['python3', 'app.py'])
        # wait some time for app to start
        time.sleep(3)

    @classmethod
    def tearDownClass(cls):
        cls.proc.kill()

    def test_group_mapping(self):
        idp, group_id = random_string(10), random_string(20)
        path = '/admin/{idp}/groups/{gid}'.format(idp=idp, gid=group_id)
        url = URL + path

        # check if one can add group mapping
        r1 = requests.put(url, json=[GROUP_DETAILS])
        self.assertEqual(r1.status_code, 204)

        # assert correct retrieve of data after correct insert
        r2 = requests.get(url)
        self.assertEqual(r2.json(), [GROUP_DETAILS])

        # check group resolving
        r3 = requests.post(URL + '/resolve_group', json=GROUP_DETAILS)
        self.assertEqual(r3.status_code, 200)
        self.assertEqual(r3.json(), {'idp': idp, 'groupId': group_id})

        # delete mapping
        r4 = requests.delete(url)
        self.assertEqual(r4.status_code, 204)

        # after delete mapping should not be available
        r5 = requests.get(url)
        self.assertEqual(r5.status_code, 404)

    def test_user_mapping(self):
        # check if one can add users mapping
        r1 = requests.post(URL + '/admin/users', json=USER_DETAILS_1)
        self.assertEqual(r1.status_code, 201)
        _, lid = r1.headers['Location'].rsplit('/', 1)
        url = URL + '/admin/users/{lid}'.format(lid=lid)

        # assert correct retrieve of data after correct insert
        r2 = requests.get(url)
        self.assertEqual(r2.json(), normalize_user_details(USER_DETAILS_1.copy()))

        # assert userDetails can be updated
        r3 = requests.put(url, json=USER_DETAILS_2)
        self.assertEqual(r3.status_code, 204)
        r4 = requests.get(url)
        self.assertEqual(r4.json(), normalize_user_details(USER_DETAILS_2.copy()))

        # set user credentials for multiple storages
        r5 = requests.put(url + '/credentials', json=MULTI_STORAGE_CREDENTIALS)
        self.assertEqual(r5.status_code, 204)

        # check normal luma
        for credentials in MULTI_STORAGE_CREDENTIALS:
            storage_id = credentials.get('storageId')
            storage_name = credentials.get('storageName')
            user_id = USER_DETAILS_2['id']
            json = {'userDetails': {'id': user_id}}
            if storage_id is not None:
                json['storageId'] = storage_id
            if storage_name is not None:
                json['storageName'] = storage_name
            r6 = requests.post(URL + '/map_user_credentials', json=json)
            self.assertEqual(r6.status_code, 200)
            awaited_credentials = {key: val
                                   for key, val in credentials.items()
                                   if key not in ('storageId', 'storageName', 'type')}
            self.assertEqual(r6.json(), awaited_credentials)

        # check reverse luma
        for credentials in MULTI_STORAGE_CREDENTIALS:
            r7 = requests.post(URL + '/resolve_user', json=credentials)
            self.assertEqual(r7.status_code, 200)
            user_details = normalize_user_details(USER_DETAILS_2)[0]
            self.assertEqual(r7.json(), {'idp': user_details['idp'],
                                         'subjectId': user_details['subjectId']})

        # delete mapping
        r8 = requests.delete(url)
        self.assertEqual(r8.status_code, 204)

        # after delete mapping should not be available
        r9 = requests.get(url)
        self.assertEqual(r9.status_code, 404)


def random_string(length):
    return ''.join(random.choice(string.ascii_uppercase + string.digits)
                   for _ in range(length))


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
