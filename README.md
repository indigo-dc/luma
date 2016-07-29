# LUMA - Local User MApping

LUMA is a REST server that exposes simple REST API that can be used to map users 
(of any system/kind) to storage specific users, in the process authorizing them 
with the storage.

New storage types are added by means of plugin system of generators. 
A generator is responsible for:

- mapping users to storage specific users
- creating a user credentials for accessing the actual storage

As of now there are three kinds of generators implemented in LUMA:

- POSIX
- Ceph
- Amazon S3
- Openstack Swift

LUMA is written using [Flask](http://flask.pocoo.org/) framework and uses 
[sqlite](https://www.sqlite.org/) backend to store information about user 
credentials.

## Luma Usage Guide

### Pairing generator with storage type or id.

LUMA requires that generator implementation must be paired with storage id or 
type. This is achieved by entry in generators_mapping. Using this pairings 
LUMA will try to choose proper generator for given request. In request user 
may provide storage_id, storage_type or both. When only storage_id is provided 
LUMA will try to find its storage_type in storage id to type mapping. Now LUMA 
will try to use storage_id (if provided) to find generator, if this fails LUMA 
will use storage_type to find generator. If no generator is found LUMA will 
respond with error. To summarize:

1. User provides generators_mapping (storage id/type to generator_id) and 
optionally storage_id to storage_type mapping.

2. LUMA receives request for mapping with storage_id, storage_type or both.

3. If only storage_id is provided LUMA tries to find its storage_type.

4. LUMA tries to find generator using storage_id.

5. If previous operation fails LUMA uses storage_type to find generator.

6. If both previous operation fails LUMA returns error, if one of operation 
succeed generator is called.

Generators results for given user_id and storage id/type will be 
cached in LUMA database.

Additionally LUMA allows to specify static `user(storageType/storageId)->credentials` 
mappings to bypass the generators for specific users. Usage of static 
mappings is described in detail in "Registering user to credentials" section.

### Initialize Database

To init LUMA server database run command:

```shell
$ ./init_db.py
```

Optional arguments:

| Param                      | Description                                           |
|:---------------------------|:------------------------------------------------------|
| -h, --help                 | help message and exit                                 |
| -c CONFIG, --config CONFIG | cfg file with app configuration (default: config.cfg) |


### Start LUMA server

To start LUMA server run command:

```shell
$ ./main.py
```

Optional arguments:

| Param                                                                        | Description                                                             |
|:-----------------------------------------------------------------------------|:------------------------------------------------------------------------|
| -h, --help                                                                   | help message and exit                                                   |
| -cm CREDENTIALS_MAPPING_FILE, --credentials-mapping CREDENTIALS_MAPPING_FILE | json file with array of credentials mappings (default:None)             |
| -gm GENERATORS_MAPPING, --generators-mapping GENERATORS_MAPPING              | json file with array of storages to generators mappings (default: None) |
| -sm STORAGES_MAPPING, --storages-mapping STORAGES_MAPPING                    | json file with array of storage id to type mappings (default: None)     |
| -c CONFIG, --config CONFIG                                                   | cfg file with app configuration (default: config.cfg)                   |


## Extending LUMA

LUMA implements support for storages by means of generators.

### Adding new generators
To support new storage or existing one in different way, user should create 
a python script in `generators` folder. All files in this folder are scanned 
by LUMA.


#### Sample Generator

Here is a sample generator for POSIX storage.


```python
import hashlib
import ConfigParser
import os

from luma.credentials import PosixCredentials

config = ConfigParser.RawConfigParser()
config.read(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), 'generators.cfg'))

LOWEST_UID = config.getint('posix', 'lowest_uid')
HIGHEST_UID = config.getint('posix', 'highest_uid')


def gen_storage_id(id):
    m = hashlib.md5()
    m.update(id)
    return LOWEST_UID + int(m.hexdigest(), 16) % HIGHEST_UID


def create_user_credentials(storage_type, storage_id, space_name, client_ip,
                            user_details):
    """Creates user credentials for POSIX storage based on provided user data.
    """
    user_id = user_details["id"]
    if user_id == "0":
        return PosixCredentials(0, 0)

    uid = gid = gen_storage_id(user_id)
    return PosixCredentials(uid, gid)
```


It has to implement function
```python
def create_user_credentials(storage_type, storage_id, space_name, client_ip, 
                            user_details):
```

and return user's credentials as oneof:

- PosixCredentials
- S3Credentials
- CephCredentials
- SwiftCredentials
  
Credentials params description:

| Storage type    | Params                   | Note                              |
|:----------------|:-------------------------|:----------------------------------|
| Posix           | uid, gid (optional)      | If gid is omitted oneprovider will try to generate gid based on space name. If this fail gid will be equal to uid. |
| Ceph            | user_name, user_key      |                                   |
| Amazon S3       | access_key, secret_key   |                                   |
| Openstack Swift | user_name, password      | Credentials to Openstack Keystone service. |

RuntimeErrors thrown in generators will be caught by LUMA and they will 
be converted to meaningful errors for the user.

In the file `generators.cfg` user can specify configuration of the generator. 
Example configuration for POSIX;

```
[posix]
lowest_uid = 1000
highest_uid = 65536
```

more examples can be found in `generators/generators.cfg.example`.


### Registering Generators

#### Pairing generator with storage_id
The generators need to be paired with specific storage by specifying a tuple of 
`storageId` (or `storageType`) and `generatorId`. 
Those mappings are located in **generators_mapping.json** and can be passed to 
luma via command line options. Example file is located in `/example_config` 
folder.

```json
[
  {
    "storageType": "Ceph",
    "generatorId": "ceph"
  },
  {
    "storageType": "Posix",
    "generatorId": "posix"
  },
  {
    "storageType": "S3",
    "generatorId": "s3"
  },
  {
    "storageType": "Swift",
    "generatorId": "swift"
  }
]
```

#### Registering id to type mapping
Additionally, one can specify a pairing of `storageId` and `storageType`. 
If LUMA fails to use a generator for a specific `storageId` it will then 
try to find one matching `storageType`.

```json
[
  {
    "storageId" : "id",
    "storageType": "type"
  },
  {
    "storageId" : "id2",
    "storageType": "type2"
  }
]

```

#### Registering user to credentials
Sometimes one might need to bypass the generators for specific users. 
LUMA allows to specify static `user(storageType/storageId)->credentials` 
mappings:

```json
[
  {
    "userId": "id",
    "storageId": "storage_id",
    "credentials": {
      "type": "Posix"  
      "uid" : 1
    }
  },
  {
    "userId": "id2",
    "storageId": "storage_id2",
    "credentials": {
      "type": "S3"  
      "accessKey": "ACCESS_KEY",
      "secretKey": "SECRET_KEY"
    }
  }
]
```

### Config
LUMA configuration file allows you to specify:

```shell
DATABASE = 'luma_database.db' # db path
HOST = '0.0.0.0' # the hostname to listen on. Set this to '0.0.0.0' to have the server available externally
PORT = 5000 # the port of the webserver. Defaults to 5000
API_KEY = 'example_api_key' # api key that must match api key from oneprovider to perform request
```

and any option described in Flask [documentation](http://flask.pocoo.org/docs/0.10/config/#builtin-configuration-values)

## LUMA API

LUMA API detailed description can be found [here](https://beta.onedata.org/docs/doc/advanced/rest/index.html).

## LUMA in Onedata
Used in [Onedata](onedata.org), LUMA allows to map Onedata user credentials 
to storage/system user credentials. By default, it is deployed as part of 
[Oneprovider](https://github.com/onedata/op-worker), however it can 
be overwritten by an external LUMA server. Admins can use an external LUMA 
server to define dedicated policies for credentials management.

## LUMA Docker Image
Every release of LUMA is published as a docker image. Here are few example 
commands how to use it:

```shell
docker run -it onedata/luma:VFS-2336

DOCKER_IP=<docker_ip>

curl -X POST -H "X-Auth-Token: example_api_key" -H "Content-Type: application/json" -d '{"spaceName":"spaceName","storageType":"Posix","userDetails":{"alias":"user.one","connectedAccounts":[],"emailList":[],"id":"1","name":"user1"}}' $DOCKER_IP:5000/map_user_credentials
curl -X POST -H "X-Auth-Token: example_api_key" -H "Content-Type: application/json" -d '{"spaceName":"spaceName","storageType":"Ceph","userDetails":{"alias":"user.one","connectedAccounts":[],"emailList":[],"id":"0","name":"user1"}}' $DOCKER_IP:5000/map_user_credentials
curl -X POST -H "X-Auth-Token: example_api_key" -H "Content-Type: application/json" -d '{"spaceName":"spaceName","storageType":"S3","userDetails":{"alias":"user.one","connectedAccounts":[],"emailList":[],"id":"1","name":"user1"}}' $DOCKER_IP:5000/map_user_credentials
curl -X POST -H "X-Auth-Token: example_api_key" -H "Content-Type: application/json" -d '{"spaceName":"spaceName","storageType":"Swift","userDetails":{"alias":"user.one","connectedAccounts":[],"emailList":[],"id":"1","name":"user1"}}' $DOCKER_IP:5000/map_user_credentials
```
