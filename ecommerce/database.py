from sqlalchemy import create_engine
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from config import *

import os

import boto3
from botocore.exceptions import ClientError


def get_secret(secret_name):

    region_name = "ap-northeast-2"

    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e
    secret = get_secret_value_response['SecretString']
    print(secret_name," : ",secret)
    
    return secret 

DBUSER = get_secret("AWS-Aurora2-DBUserName")
PASSWORD = get_secret("AWS-Aurora2-DBPassword")
PRIMARY_HOST = get_secret("AWS-Aurora2-ClusterEndpoint")
READONLY_HOST = get_secret("AWS-Aurora2-ReaderEndpoint")
PORT = os.getenv("PORT")
DBNAME = os.getenv("DBNAME")

PRIMARY_DB_URL = f'mysql+pymysql://{DBUSER}:{PASSWORD}@{PRIMARY_HOST}:{PORT}/{DBNAME}'
READONLY_DB_URL = f'mysql+pymysql://{DBUSER}:{PASSWORD}@{READONLY_HOST}:{PORT}/{DBNAME}'


class PrimaryEngineConn:
    def __init__(self):
        self.engine = create_engine(PRIMARY_DB_URL, pool_size=30, max_overflow=1000, pool_recycle=500)
        self.Session = sessionmaker(bind=self.engine)

    def get_session(self):
        session = self.Session()
        try:
            yield session
        finally:
            session.close()

class ReadonlyEngineConn:
    def __init__(self):
        self.engine = create_engine(READONLY_DB_URL, pool_size=30, max_overflow=1000, pool_recycle=500)
        self.Session = sessionmaker(bind=self.engine)

    def get_session(self):
        session = self.Session()
        try:
            yield session
        finally:
            session.close()            


# class engineconn:

#     def __init__(self):
#         self.engine = create_engine(DB_URL, pool_size=30, max_overflow=1000, pool_recycle=500)
#         self.Session = sessionmaker(bind=self.engine)
#         self.session = self.Session()
#         self.conn = self.engine.connect()

#     def get_session(self):
#         return self.session

#     def get_connection(self):
#         return self.conn
    
# class engineconn:

#     def __init__(self):
#         self.engine = create_engine(DB_URL, pool_size=100, max_overflow=1000, pool_recycle = 500)

#     def sessionmaker(self):
#         Session = sessionmaker(bind=self.engine)
#         session = Session()
#         return session

#     def connection(self):
#         conn = self.engine.connect()
#         return conn
