import socket
import struct
import pickle
import random
import traceback

from utils.constants import Constants
from utils.exceptions import ServersNotFoundException
from utils.logger import logger


class ClientKeyValueStore:
    def __init__(self, id):
        self._id = id

        self._write_set = {}
        self._read_set = {}
        self._transaction_id = 0

        self._socket = None
        self._server_address, self._server_port, _, _ = self._choose_random_server()

    def _choose_random_server(self):
        logger.info('Attempting to choose a random server from all servers available.')
        servers = self._fetch_all_servers()

        for i in range(len(servers)):
            if servers[i][0] == Constants.SERVER_SEQUENCER_ADDRESS and servers[i][1] == Constants.SERVER_SEQUENCER_PORT:
                del servers[i]
                break

        random_server = random.choice(servers)
        logger.info(f'Random server chosen -> {random_server}')

        return random_server

    def _fetch_all_servers(self):
        logger.info('Attempting to fetching all servers from server discoverer')
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((Constants.SERVER_DISCOVERER_ADDRESS, Constants.SERVER_DISCOVERER_PORT))

            addr, port = s.getsockname()
            message = struct.pack(Constants.SERVER_DISCOVERER_REQUEST_FORMAT, 2, socket.inet_aton(addr), port, socket.inet_aton(addr), port)

            logger.info(f'Sending request for all servers to server discoverer. Message -> {message}')
            s.send(message)

            response = b''
        
            while True:
                packet = s.recv(4096)

                if not packet:
                    break

                logger.info(f'Received response from server discoverer. Response -> {packet}')
                response += packet

        servers = pickle.loads(response)

        if len(servers) == 0:
            raise ServersNotFoundException()

        logger.info(f'Deserialized fetch servers response from server discoverer -> {servers}')
        return servers

    def read(self, item):
        logger.info(f'Attempting to read item {item}')

        value = self._write_set.get(item)
        if value:
            logger.info('Item already in local write set')
            return value

        value = self._read_set.get(item)
        if value:
            logger.info('Item already in local read set')
            return value

        value, version = self._read_from_server(item)

        if value is None and version is None:
            logger.error('Item not found in local sets or remote server')
            return None

        logger.info(f'Item read from server: Value -> {value}, Version -> {version}')
        self._read_set[item] = (value, version)

        return value

    def _read_from_server(self, item):
        logger.info('Attempting to read from server KVS.')
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(20)

                s.connect((self._server_address, self._server_port))

                message = struct.pack(Constants.READ_REQUEST_FORMAT, 0, item.encode('utf-8'))
                logger.info(f'Sending request for value to server KVS. Address -> {self._server_address}, Port -> {self._server_port}, Message -> {message}')
                s.sendall(message)

                data = s.recv(4096)
        except Exception as e:
            logger.warning('Attempt to read from server KVS failed. Attempting to find another server.')

            self._server_address, self._server_port, _, _ = self._choose_random_server()

            return self._read_from_server(item)

        if not data:
            logger.info('Server KVS did not return any values')
            return None, None

        version = struct.unpack(Constants.READ_RESPONSE_INITIAL_FORMAT, data[:4])[0]
        value = pickle.loads(data[4:])

        return value, version

    def write(self, item, value):
        logger.info(f'Writing to write set. Item {item}, Value {value}')
        self._write_set[item] = value

    def abort(self):
        logger.info('Abort! Resetting transaction state.')
        self._reset_transaction()

    def commit(self):
        logger.info(f'Client commit in progress -> Write set: {self._write_set}, Read set: {self._read_set}')
        data = pickle.dumps((self._write_set, self._read_set))

        logger.info('Creating a socket to receive server commit or abort message')
        awaiting_response_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        awaiting_response_socket.bind(('127.0.0.1', 0))
        awaiting_response_socket.listen()

        ar_socket_address, ar_socket_port = awaiting_response_socket.getsockname()
        logger.info(f'Client created response socket -> Address {ar_socket_address}, Port {ar_socket_port}')

        message = struct.pack(Constants.DELIVER_REQUEST_INITIAL_FORMAT, 1, socket.inet_aton(ar_socket_address), ar_socket_port, self._transaction_id)
        message += data

        for server_address, server_port, _, _ in self._fetch_all_servers():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                logger.info(f'Client sending commit to server. Address -> {server_address}, Port -> {server_port}, Message -> {message}')
                s.connect((server_address, server_port))

                s.send(message)

        connection, _ = awaiting_response_socket.accept()

        try:
            data = connection.recv(1)
            logger.info(f'Client received response from server -> {data}')

            if data == b'0':
                logger.warning('Transaction aborted!')
            else:
                logger.info('Transaction committed!')
        except Exception as e:
                logger.error(f'Client KVS -> An error occurred: {e}')
                traceback.print_exc()
        finally:
            awaiting_response_socket.close()

        self._reset_transaction()

    def _reset_transaction(self):
        logger.info('Cleaning read set, write set, and jumping to next transaction')
        self._read_set = {}
        self._write_set = {}
        self._transaction_id += 1
