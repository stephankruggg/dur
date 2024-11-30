import os
import shelve
import socket
import struct
import traceback
import pickle

from src.utils.constants import Constants

class ServerKeyValueStore:
    def __init__(self, id):
        self._last_commited = 0

        self._id = id
        self._address = Constants.SERVER_KEY_VALUE_STORE_ADDRESS
        self._port = Constants.SERVER_KEY_VALUE_STORE_BASE_PORT + self._id

        self._load_initial_database()
        self._connect_to_server_discoverer()

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind((self._address, self._port))
        self._socket.listen(3)

        self._run()

    def _load_initial_database(self):
        self._database_path = Constants.FOLDER_NAME / str(Constants.EXAMPLE_INSTACE) / f'server{self._id}'

        os.makedirs(self._database_path, exist_ok=True)
        print('Server folder successfully initialized!')

        source_path = Constants.FOLDER_NAME / str(Constants.EXAMPLE_INSTACE) / 'data'
        if not os.path.isfile(source_path):
            print('No model DB provided. Skipping creating a copy.')
            return

        with shelve.open(source_path) as source:
            with shelve.open(self._database_path / 'db') as destination:
                for key, value in source.items():
                    destination[key] = value
                    print((key, value))

        print('Data successfully copied from model DB!')

    def _connect_to_server_discoverer(self):
        print('Attempting to get known by the server discoverer.')

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((Constants.SERVER_DISCOVERER_ADDRESS, Constants.SERVER_DISCOVERER_PORT))

            message = struct.pack(Constants.SERVER_DISCOVERER_REQUEST_FORMAT, 0, socket.inet_aton(self._address), self._port)

            s.send(message)
            print('Server now known!')

    def _run(self):
        while True:
            print('KVS Server listening...')

            connection, address = self._socket.accept()
            print(f'KVS Server connected to {address}')

            # To do: Transform this into separate thread
            try:
                data = connection.recv(4096)

                if data[0] == 0:
                    self._fetch_value(data, connection)
                elif data[0] == 1:
                    self._deliver_transaction(data)
            except Exception as e:
                print(f'Server KVS -> An error occurred: {e}')
                traceback.print_exc()

    def _fetch_value(self, data, connection):
        item = data[1:].decode('utf-8').strip('\x00')

        try:
            with shelve.open(Constants.FOLDER_NAME / str(Constants.EXAMPLE_INSTACE) / f'server{self._id}' / 'db') as db:
                version, value = db[item]

            message = struct.pack(Constants.READ_RESPONSE_INITIAL_FORMAT, version)
            message += pickle.dumps(value)
        except KeyError:
            print(f'Item {item} not found in database.')
            connection.close()
            return

        connection.sendall(message)

    def _deliver_transaction(self, data):
        _, requester_address, requester_port = struct.unpack(Constants.DELIVER_REQUEST_INITIAL_FORMAT, data[:7])
        requester_address = socket.inet_ntoa(requester_address)

        write_set, read_set = pickle.loads(data[7:])

        with shelve.open(Constants.FOLDER_NAME / str(Constants.EXAMPLE_INSTACE) / f'server{self._id}' / 'db') as db:
            for key, value in read_set.items():
                try:
                    if db[key][0] > value[1]:
                        self._respond_to_client(requester_address, requester_port, False)
                        return
                except KeyError:
                    pass

            self._last_commited += 1

            for key, value in write_set.items():
                try:
                    next_version = db[key][0] + 1
                except KeyError:
                    next_version = 0

                db[key] = (next_version, value)

        self._respond_to_client(requester_address, requester_port, True)

    def _respond_to_client(self, address, port, commit):
        if commit:
            print('Attempting to send commit message to client.')
            message = b'1'
        else:
            print('Attempting to send abort message to client.')
            message = b'0'

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                print(f'Server connecting to client -> Address {address}, Port {port}')
                s.connect((address, port))

                print(f'Server sending message -> {message}')
                s.send(message)
        except Exception as e:
            # To do: Connection will be closed on client side if already received commit or abort. Treat error better.
            print(f'Server KVS -> An error occurred when responding to client: {e}')
            traceback.print_exc()
