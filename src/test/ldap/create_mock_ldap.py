from ldap3 import Server, Connection, ALL_ATTRIBUTES, MOCK_SYNC, OFFLINE_AD_2012_R2
import getpass

"""
This script can be used to generate the JSON files required for testing the LDAP connection against a mock LDAP server.
A Jax real username and password is required the first time around in order to correctly create the files.
These files will simulate the production LDAP response.
"""

REAL_SERVER = 'ldaps://ldaps.jax.org:636'
DOMAIN_NAME = 'jax.org'

MOCK_INFO = 'mock_ldap_info.json'
MOCK_SCHEMA = 'mock_ldap_schema.json'
MOCK_ENTRIES = 'mock_ldap_entries.json'

print('Enter Jax credentials')
username = input('Username: ')
password = getpass.getpass()

# Retrieve server info and schema from a real server
server = Server(REAL_SERVER, get_info=OFFLINE_AD_2012_R2, use_ssl=True)
connection = Connection(server, f'{username}@{DOMAIN_NAME}', password, auto_bind=True, authentication='SIMPLE',
                        client_strategy='SYNC', auto_referrals=False, check_names=True, read_only=True, lazy=False,
                        raise_exceptions=True)

# Store server info and schema to json files
server.info.to_file(MOCK_INFO)
server.schema.to_file(MOCK_SCHEMA)

# Read entries from a portion of the DIT from real server and store them in a json file
if connection.search('DC=jax,DC=org', f'(sAMAccountName={username})', attributes=ALL_ATTRIBUTES):
    connection.response_to_file(MOCK_ENTRIES, raw=True)

# Close the connection to the real server
connection.unbind()

# Create a fake server from the info and schema json files
fake_server = Server.from_definition('my_fake_server', MOCK_INFO, MOCK_SCHEMA)

# Create a MockSyncStrategy connection to the fake server
fake_connection = Connection(fake_server, client_strategy=MOCK_SYNC)

# Populate the DIT of the fake server by adding at runtime an entry
fake_connection.strategy.add_entry(
    'CN=The Test User testuser,OU=Users,OU=Departments,OU=Bar_Harbor,DC=jax,DC=org',
        {
            'userPassword': 'pa55word',
            'givenName': 'Test',
            'mail': 'test.user@jax.org',
            'memberOf': [
                "CN=CGRP-bhcape01,OU=Groups,DC=jax,DC=org",
                "CN=O365-Faculty-A1-Base,OU=Microsoft,OU=Cloud,OU=Groups,DC=jax,DC=org",
                "CN=BOX-JAX_All_Users,OU=Microsoft,OU=Cloud,OU=Groups,DC=jax,DC=org",
                "CN=GRP-BH_HDrive_Migration,OU=Domain_Local,OU=Groups,DC=jax,DC=org",
                "CN=GRP-WebExUsers,OU=Microsoft,OU=Cloud,OU=Groups,DC=jax,DC=org",
                "CN=GRP-AAD-IT-Pilot,OU=Groups,DC=jax,DC=org",
                "CN=VPN-2FA,OU=Domain_Global,OU=Groups,DC=jax,DC=org",
                "CN=Exchange 2013 Users,OU=Distribution Groups,OU=Groups,DC=jax,DC=org",
                "CN=cs-all,OU=Distribution Groups,OU=Groups,DC=jax,DC=org",
                "CN=cssa,OU=Distribution Groups,OU=Groups,DC=jax,DC=org",
                "CN=ADM-StrictPasswords,OU=AD_Admin,OU=Groups,DC=jax,DC=org",
                "CN=FASPEX-USERS,OU=Unix,OU=Groups,DC=jax,DC=org",
                "CN=CGRP-donkey,OU=Unix,OU=Groups,DC=jax,DC=org",
                "CN=cssc,OU=Distribution Groups,OU=Groups,DC=jax,DC=org"
            ],
            "sn": [
                "testuser_sn"
            ],
            'objectClass': [
                "top",
                "person",
                "organizationalPerson",
                "user"
            ],
            'sAMAccountName': [
                "testuser"
            ]
        })
# Add another fake user for Simple binding
fake_connection.strategy.add_entry('cn=my_user,ou=test,o=lab', {'userPassword': 'my_password', 'sn': 'user_sn', 'revision': 0})
# or by reading the JSON entries file
fake_connection.strategy.entries_from_json(MOCK_ENTRIES)

# Bind to the fake server
fake_connection.bind()

fake_connection.search('DC=jax,DC=org', '(sAMAccountName=testuser)', attributes=ALL_ATTRIBUTES)

entries = fake_connection.entries
# do something


fake_connection.unbind()
