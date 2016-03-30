import os
import ConfigParser

config = ConfigParser.RawConfigParser()
config.read(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), 'generators.cfg'))

USER = config.get('ceph', 'user')
KEY = config.get('ceph', 'key')


def create_user_credentials(global_id, storage_type, storage_id, source_ips,
                            source_hostname, user_details):
    """Creates user credentials for CEPH storage based on provided user data.
    Sample output:
    {
        "user_name": "USER",
        "user_key": "KEY"
    }
    """
    return {"user_name": USER, "user_key": KEY}

