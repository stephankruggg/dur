import socket
import struct
import pickle
import random
import traceback

from src.utils.constants import Constants

class ClientKeyValueStore:
    def __init__(self, id):
        self._id = id

        self._write_set = {}
        self._read_set = {}
        self._transaction_id = 0

        self._socket = None
        self._server_address, self._server_port = self._choose_random_server()

    def _choose_random_server(self):
        servers = self._fetch_all_servers()

        return random.choice(servers)

    def _fetch_all_servers(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((Constants.SERVER_DISCOVERER_ADDRESS, Constants.SERVER_DISCOVERER_PORT))

            addr, port = s.getsockname()
            message = struct.pack(Constants.SERVER_DISCOVERER_REQUEST_FORMAT, 2, socket.inet_aton(addr), port)

            s.send(message)

            response = b''
        
            while True:
                packet = s.recv(4096)

                if not packet:
                    break

                response += packet

        return pickle.loads(response)

    def read(self, item):
        value = self._write_set.get(item)
        if value:
            return value

        value = self._read_set.get(item)
        if value:
            return value

        value, version = self._read_from_server(item)

        if value is None and version is None:
            print('Item not found')
            return None

        self._read_set[item] = (value, version)

        return value

    def _read_from_server(self, item):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self._server_address, self._server_port))

            message = struct.pack(Constants.READ_REQUEST_FORMAT, 0, item.encode('utf-8'))
            s.sendall(message)

            data = s.recv(4096)

        if not data:
            return None, None

        version = struct.unpack(Constants.READ_RESPONSE_INITIAL_FORMAT, data[:4])[0]
        value = pickle.loads(data[4:])

        return value, version

    def write(self, item, value):
        self._write_set[item] = value

    def abort(self):
        self._reset_transaction()

    def commit(self):
        print(f'Client commit in progress -> Write set: {self._write_set}, Read set: {self._read_set}')
        data = pickle.dumps((self._write_set, self._read_set))

        awaiting_response_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        awaiting_response_socket.bind(('127.0.0.1', 0))
        awaiting_response_socket.listen()

        ar_socket_address, ar_socket_port = awaiting_response_socket.getsockname()
        print(f'Client created response socket -> Address {ar_socket_address}, Port {ar_socket_port}')

        message = struct.pack(Constants.DELIVER_REQUEST_INITIAL_FORMAT, 1, socket.inet_aton(ar_socket_address), ar_socket_port)
        message += data

        for server_address, server_port in self._fetch_all_servers():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                print(f'Client sending commit to server -> Address {server_address}, Port {server_port}')
                s.connect((server_address, server_port))

                s.send(message)

        connection, _ = awaiting_response_socket.accept()
        print('Client received response from server.')
        try:
            data = connection.recv(1)

            if data == b'0':
                print('Transaction aborted!')
            else:
                print('Transaction committed!')
        except Exception as e:
                print(f'Client KVS -> An error occurred: {e}')
                traceback.print_exc()
        finally:
            awaiting_response_socket.close()

        self._reset_transaction()

    def _reset_transaction(self):
        self._write_set = {}
        self._read_set = {}
        self._transaction_id += 1
