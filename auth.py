import boto3
import botocore.exceptions
import hashlib

CLIENT_ID = "1iucgb9qtnf9i880tqe6ga6a01"
USER_POOL_ID = "us-west-2_ztWiNsONr"


class Client:
    def __init__(self, conn, addr):
        super().__init__()
        self.is_login = False
        self.username = None
        self.conn = conn
        self.addr = addr

    def set_login_stat(self, value):
        self.is_login = value

    def set_username(self, value):
        self.username = value

    def set_userid(self, value):
        self.uid = value

    def get_login_stat(self):
        return self.is_login

    def get_username(self):
        return self.username

    def get_userid(self):
        return self.uid


class UserPool:
    def __init__(self):
        self.client = boto3.client('cognito-idp')

    def encode_password(self, password):
        hash_key = "nctu_bbs".encode()
        encode_password = hashlib.sha256(hash_key)
        encode_password.update(password.encode())
        return encode_password.hexdigest()

    def create_user(self, username, email, password):
        self.client.admin_create_user(
            UserPoolId=USER_POOL_ID,
            Username=username,
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': email
                },
            ]
        )
        self.client.admin_set_user_password(
            UserPoolId=USER_POOL_ID,
            Username=username,
            Password=self.encode_password(password),
            Permanent=True
        )

    def delete_user(self, username):
        self.client.admin_delete_user(
            UserPoolId=USER_POOL_ID,
            Username=username
        )

    def login(self, username, password):
        response = self.client.admin_initiate_auth(
            UserPoolId=USER_POOL_ID,
            ClientId=CLIENT_ID,
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                     'USERNAME': username,
                     'PASSWORD': self.encode_password(password)
            }
        )


if __name__ == "__main__":
    user_pool = UserPool()
    user_pool.login("test", "test1")
