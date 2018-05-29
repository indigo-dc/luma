# LUMA - Local User MApping

LUMA is a REST server that exposes simple REST API that can be used to map users 
(of any system/kind) to storage specific users, in the process authorizing them
with the storage.



This is an example implementation, which should be tailored or implemented from
scratch for specific purposes.


POSIX
Ceph
Amazon S3
Openstack Swift


## Installation

### Docker image

The easiest way to setup LUMA is using the provided Docker image, which can 
be simply started as follows:

```
$ touch db.json # Create persistent database file
$ docker run -d --net=host -v $PWD/db.json:/luma/db.json onedata/luma:17.06.0-rc6
```

### Natively using python

LUMA can be also started directly using Python 3 without Docker as follows:
```
$ sudo pip3 install -U connexion
$ python3 app.py
```

## Usage

Once LUMA is running, it's API can be called using any REST client (e.g. cURL),
or it can be directly operated using the automatically generated GUI available
at:

```
http://<HOST>:8080/api/v3/luma/ui/
```

Mappings can be added using REST `/admin` endpoints or directly edited in the
`db.json` file.


Below are some example operations on LUMA using cURL:

### Add user with Onedata ID. 
The user account is now a resource in Luma, the id of this resource is returned 
in location header.

```
curl -X POST --header 'Content-Type: application/json' --header 'Accept: application/json' -d '{ \
   "id": "9743a66f914cc249efca164485a19c5c" \
 }' 'http://192.168.1.200:8080/api/v3/luma/admin/users'

```

where `"id"` is an id of a user in Onedata. This operation returns an internal LUMA user id in 
`Location` header, which must be used for further administrative calls.

### Set user credentials to a POSIX storage.

```
curl -X PUT --header 'Content-Type: application/json' --header 'Accept: application/json' -d '[ \
   { \
     "id": "1", \
     "type": "posix", \
     "uid": 1001, \
     "gid": 1001 \
   } \
 ]' 'http://192.168.1.200:8080/api/v3/luma/admin/users/1/credentials'

```

### Set user credentials to an S3 bucket

```
curl -X PUT --header 'Content-Type: application/json' --header 'Accept: application/json' -d '[ \
   { \
     "id": "2", \
     "type": "s3", \
     "accessKey": "ABCD", \
     "secretKey": "1234" \
   } \
 ]' 'http://192.168.1.200:8080/api/v3/luma/admin/users/1/credentials'

```


### Set user credentials to a Ceph storage

```
curl -X PUT --header 'Content-Type: application/json' --header 'Accept: application/json' -d '[ \
   { \
     "id": “3”, \
     "type": "ceph", \
     "key": "ABCD", \
     "username": "user1" \
   } \
 ]' 'http://192.168.1.200:8080/api/v3/luma/admin/users/1/credentials'
```

### Set user credentials to a GlusterFS storage

```
curl -X PUT --header 'Content-Type: application/json' --header 'Accept: application/json' -d '[ \
   { \
     "id": "1", \
     "type": "glusterfs", \
     "uid": 1001, \
     "gid": 1001 \
   } \
 ]' 'http://192.168.1.200:8080/api/v3/luma/admin/users/1/credentials'

```


### Editing database JSON manually

LUMA database is has a very simple structure which if preferred can be created manually or using
scripts and added to LUMA before starting the service. Example structure of LUMA database is 
presented below:

```
{
  "_default": {},
  "users": {
    "1": {
      "userDetails": [
        {
          "login": "user.one",
          "name": "user1",
          "idp": "onedata",
          "subjectId": "9743a66f914cc249efca164485a19c5c"
        }
      ],
      "credentials": [
        {
          "storageId": "1",
          "type": "posix",
          "uid": 1001,
          "gid": 1001
        },
        {
          "storageId": “2”,
          "type": “s3”,
          “accessKey”: 1001,
          “secretKey”: 1001
        },
        {
          "storageId": “3”,
          "type": "posix",
          "uid": 1001,
          "gid": 1001
        }
      ]
    }
  },
  "groups": {
    "1": {
      "idp": "5da4aaa1-5cd3-4e33-92b6-89589e997974",
      "gid": "a514ccef-fb96-4e65-b786-5d503ff04c45",
      "groupDetails": [
        {
          "gid": 1001,
          "name": "users",
          "storageId": "1"
        }
      ]
    }
  }
}

```
