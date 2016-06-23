import ConfigParser
import os

config = ConfigParser.RawConfigParser()
config.read(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), 'generators.cfg'))

USER_NAME = config.get('swift', 'user_name')
PASSWORD = config.get('swift', 'password')


def create_user_credentials(global_id, storage_type, storage_id, space_name,
                            source_ips, source_hostname, user_details):
    """Creates user credentials for Swift storage based on provided user data.
    Sample output:
    {
        "user_name": "USER_NAME",
        "password": "PASSWORD"
    }
    """
    return {
        'user_name': USER_NAME,
        'password': PASSWORD
    }
