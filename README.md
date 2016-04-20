# LUMA - Local User MApping

LUMA is a REST server that exposes simple REST API that can be used to map users (of any system/kind) to storage specific users, in the process authorizing them with the storage.

New storage types are added by means of plugin system of generators. A generator is responsible for:

- mapping users to storage specific users
- creating a user credentials for accessing the actual storage

As of now there are three kinds of generators implemented in LUMA:

- POSIX
- Ceph
- Amazon S3

LUMA is written using [Flask](http://flask.pocoo.org/) framework and uses [sqlite](https://www.sqlite.org/) backend to store information about user credentials.

## Luma Usage Guide
### Initialize Database

To init LUMA server database run command:

```shell
$ ./init_db.py
```

Optional arguments:

| Param                      | Description                              |
| :------------------------- | :--------------------------------------- |
| -h, --help                 | help message and exit                    |
| -c CONFIG, --config CONFIG | cfg file with app configuration (default: config.cfg) |


### Start LUMA server

To start LUMA server run command:

```shell
$ ./main.py
```

Optional arguments:

| Param                                    | Description                              |
| ---------------------------------------- | :--------------------------------------- |
| -h, --help                               | help message and exit                    |
| -cm CREDENTIALS_MAPPING_FILE, --credentials-mapping CREDENTIALS_MAPPING_FILE | json file with array of credentials mappings (default:None) |
| -gm GENERATORS_MAPPING, --generators-mapping GENERATORS_MAPPING | json file with array of storages to generators mappings (default: None) |
| -sm STORAGES_MAPPING, --storages-mapping STORAGES_MAPPING | json file with array of storage id to type mappings (default: None) |
| -c CONFIG, --config CONFIG               | cfg file with app configuration (default: config.cfg) |


## Extending LUMA

LUMA implements support for storages by means of generators. 

### Adding new generators
To support new storage or existing one in different way, user should create a python script in `generators` folder. All files in this folder are scanned by LUMA.


#### Sample Generator

Here is a sample generator for POSIX storage.


```python
import hashlib
import ConfigParser
import os

config = ConfigParser.RawConfigParser()
config.read(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), 'generators.cfg'))

LowestUID = config.getint('posix', 'lowest_uid')
HighestUID = config.getint('posix', 'highest_uid')


def gen_storage_id(id):
    m = hashlib.md5()
    m.update(id)
    return LowestUID + int(m.hexdigest(), 16) % HighestUID


def create_user_credentials(global_id, storage_type, storage_id, source_ips,
                            source_hostname, user_details):
    """Creates user credentials for POSIX storage based on provided user data.
    Sample output:
    {
        "uid": 31415
    }
    """
    if global_id == "0":
        return {'uid': 0}

    return {'uid': gen_storage_id(global_id)}
```


It has to implement functon

```python
def create_user_credentials(global_id, storage_type, storage_id, source_ips, source_hostname, user_details)
```

and return user's credentials as a DICT. For a detailed explanation of arguments, refer to REST API bellow (credentials field in successfull responses).

RuntimeErrors thrown in generators will be caucht by LUMA and it will be converted to a meaningfull error for the user.

In the file `generators.cfg` user can specify configuration of the generator. Example configuration for POSIX;

```
[posix]
lowest_uid = 1000
highest_uid = 65536
```

more examples can be found in `generators/generators.cfg.example`.


### Registering Generators

#### Pairing generator with storage_id
The generators needs to be paired with specyfic storage by specifying a tuple of `storage_id` and `generator_id` (storage type may be provided as `storage_id`).  Those mappings are located in **generators_mapping.json** Example file is located in `/example_config` folder.

```json
[
  {
    "storage_id": "Ceph",
    "generator_id": "ceph"
  },
  {
    "storage_type": "DirectIO",
    "generator_id": "posix"
  },
  {
    "storage_type": "AmazonS3",
    "generator_id": "s3"
  }
]
```

#### Registering id to type mapping
Additionally one can specify a pairing of `storage_id` and `storage_type`. If LUMA fails to use a generator for a specyifc `storage_id` it will then try to find one matching `storage_type`.

```json
[
  {
    "storage_id" : "id",
    "storage_type": "type"
  },
  {
    "storage_id" : "id2",
    "storage_type": "type2"
  }
]

```

#### Registering user to credentials
Sometimes one might need to bypass the generators for specific users. LUMA allows to specify static `user(storage_type/id)->credentials` mappings:

```json
[
  {
    "global_id": "id",
    "storage_id": "storage_id",
    "posix": {
      "uid" : 1
    }
  },
  {
    "global_id": "id2",
    "storage_id": "storage_id2",
    "credentials": { 
      "access_key": "ACCESS_KEY", 
      "secret_key": "SECRET_KEY" 
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
```
and any option described in Flask [documentation](http://flask.pocoo.org/docs/0.10/config/#builtin-configuration-values)

## LUMA API

### Get User Credentials


Returns json with user credentials to storage. Use `GET` method.

#### URL

```shell
 /get_user_credentials
```

#### URL Params

| Param           | Description                              |
| :-------------- | :--------------------------------------- |
| global_id       | user global id                           |
| storage_type    | storage type e.g. `Ceph`                 |
| storage_id      | storage id (storage type may be provided instead of id) |
| source_ips      | IPs list of provider performing query as string encoded JSON |
| source_hostname | hostname of provider performing query    |
| user_details    | detail information of user as string encoded JSON |

**NOTE:** One of `storage_id`, `storage_type` may be omitted in request.

User details:

* id
* name
* connected_accounts - list of open id acconts, each containing: 
	* provider_id
    * user_id
    * login
    * name
    * email_list
* alias
* email_list 

### Success Response:

* **Code:** 200 OK <br />
  **Content:**
  * POSIX

  ```json
  {
      "status": "success",
      "credentials": {
          "uid": 31415
      }
  }
  ```
  * CEPH

  ```json
  {
      "status": "success",
      "credentials": {
          "access_key": "ACCESS_KEY",
          "secret_key": "SECRET_KEY"
      }
  }
  ```
  * AMAZON S3

  ```json
  {
      "status": "success",
      "credentials": {
          "user_name": "USER",
          "user_key": "KEY"
      }
  }
  ```

### Error Response:

* **Code:** 422 Unprocessable Entity <br />
  **Content:** `{ "status: "error", "message": "Missing parameter global_id" }`

  OR

* **Code:** 500 Internal Server Error <br />
  **Content:** `{ "status: "error", "message": "MESSAGE" }`

## LUMA in Onedata
Used in [Onedata](onedata.org), LUMA allows to map Onedata user credentials to storage/system user credentials. By default, it is deployed as part of [Oneprovider](https://github.com/onedata/op-worker), however it can be overwritten by an external LUMA server. Admins can use an external LUMA server to define dedicated policies for credentials management.

## LUMA Docker Image
Every release of LUMA is published as a docker image. Here are few example commands how to use it:
```shell
docker run -it docker.onedata.org/luma:a1ee3b1

curl --get -d global_id=1 -d storage_type=DirectIO -d source_hostname=hostname -d source_ips=[] -d user_details={}  172.17.0.12:5000/get_user_credentials
curl --get -d global_id=0 -d storage_type=Ceph -d source_hostname=hostname -d source_ips=[] -d user_details={}  172.17.0.12:5000/get_user_credentials
curl --get -d global_id=1 -d storage_type=AmazonS3 -d source_hostname=hostname -d source_ips=[] -d user_details={}  172.17.0.12:5000/get_user_credentials
```


