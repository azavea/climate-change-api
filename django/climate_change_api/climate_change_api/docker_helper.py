import socket
import os
from time import sleep

DATABASE_HOST = os.getenv('CC_DB_HOST', 'postgres')
DATABASE_PORT = int(os.getenv('CC_DB_PORT', 5432))


def wait_for_database():
    success = False
    while not success:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((DATABASE_HOST, DATABASE_PORT))
            s.close()
            success = True
        except socket.error:
            sleep(20)
