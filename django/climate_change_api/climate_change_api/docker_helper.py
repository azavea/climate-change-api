import socket
from time import sleep

DATABASE_HOST = 'postgres'
DATABASE_PORT = 5432


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
