import os
import shelve
import socket
import struct
import traceback
import pickle
import threading

from utils.constants import Constants
from utils.logger import logger


class ServerKeyValueStore:
    def __init__(self, id):
        self._last_commited = 0
        self._holdback = {}
        self._sequence_number = 0

        self._id = id
        self._address = Constants.SERVER_KEY_VALUE_STORE_ADDRESS
        self._port = Constants.SERVER_KEY_VALUE_STORE_BASE_PORT + self._id

        self._sequence_number_address = Constants.SERVER_KEY_VALUE_STORE_SN_ADDRESS
        self._sequence_number_port = Constants.SERVER_KEY_VALUE_STORE_SN_PORT + self._id

        self._load_initial_database()
        self._connect_to_server_discoverer()

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind((self._address, self._port))
        self._socket.listen(3)

        self._sequence_number_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sequence_number_socket.bind((self._sequence_number_address, self._sequence_number_port))
        self._sequence_number_socket.listen(3)

        self._holdback_lock = threading.Lock()

        threading.Thread(target=self._receive_sequence_numbers).start()

        self._run()

    def _load_initial_database(self):
        self._database_path = Constants.FOLDER_NAME / str(Constants.EXAMPLE_INSTACE) / f'server{self._id}'

        os.makedirs(self._database_path, exist_ok=True)
        logger.info('Server folder successfully initialized!')

        source_path = Constants.FOLDER_NAME / str(Constants.EXAMPLE_INSTACE) / 'data'
        if not os.path.isfile(source_path):
            logger.warning('No model DB provided. Skipping creating a copy.')
            return

        with shelve.open(source_path) as source:
            with shelve.open(self._database_path / 'db') as destination:
                for key, value in source.items():
                    destination[key] = value
                    print((key, value))

        logger.info('Data successfully copied from model DB!')

    def _connect_to_server_discoverer(self):
        logger.info('Attempting to get known by the server discoverer.')

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((Constants.SERVER_DISCOVERER_ADDRESS, Constants.SERVER_DISCOVERER_PORT))

            message = struct.pack(Constants.SERVER_DISCOVERER_REQUEST_FORMAT, 0, socket.inet_aton(self._address), self._port, socket.inet_aton(self._sequence_number_address), self._sequence_number_port)

            s.send(message)

            logger.info('Server now known!')

    def _receive_sequence_numbers(self):
        while True:
            connection, _ = self._sequence_number_socket.accept()

            with connection:
                data = connection.recv(4096)

                address, port, t_id, sn = struct.unpack(Constants.SERVER_SEQUENCER_FORMAT, data)
                address = socket.inet_ntoa(address)

                logger.info(f'Server KVS received sequence number {sn} for: Address {address}, Port {port}, Transaction ID {t_id}')

            logger.info(f'Server KVS updating holdback')
            self._holdback[(address, port, t_id)] = sn

            logger.info('Server KVS notifying all listeners of the holdback update')
            self._holdback_lock.release()

    def _run(self):
        while True:
            logger.info('KVS Server listening...')

            connection, address = self._socket.accept()
            logger.info(f'KVS Server connected to {address}')

            # To do: Transform this into separate thread (necessary)
            try:
                data = connection.recv(4096)

                if data[0] == 0:
                    self._fetch_value(data, connection)
                elif data[0] == 1:
                    self._deliver_transaction(data)
            except Exception as e:
                logger.error(f'Server KVS -> An error occurred: {e}')
                traceback.print_exc()

    def _fetch_value(self, data, connection):
        item = data[1:].decode('utf-8').strip('\x00')

        logger.info(f'Server KVS attempting to find item -> {item}')
        try:
            with shelve.open(Constants.FOLDER_NAME / str(Constants.EXAMPLE_INSTACE) / f'server{self._id}' / 'db') as db:
                version, value = db[item]

            logger.info(f'Server KVS found item {item} -> Version {version}, Value {value}')
            message = struct.pack(Constants.READ_RESPONSE_INITIAL_FORMAT, version)
            message += pickle.dumps(value)
        except KeyError:
            logger.error(f'Item {item} not found in database.')
            connection.close()
            return

        logger.info(f'Server KVS sending value of item {item}')
        connection.sendall(message)

    def _deliver_transaction(self, data):
        _, requester_address, requester_port, message_id = struct.unpack(Constants.DELIVER_REQUEST_INITIAL_FORMAT, data[:11])
        requester_address = socket.inet_ntoa(requester_address)

        write_set, read_set = pickle.loads(data[11:])

        logger.info(f'Server KVS received commit from {requester_address}:{requester_port} -> Transaction ID {message_id}, Write set {write_set}, Read set {read_set}')

        holdback_key = (requester_address, requester_port, message_id)

        while holdback_key not in self._holdback.keys() or self._holdback[holdback_key] != self._sequence_number:
            logger.info(f'Server KVS waiting for sequence number for transaction {message_id}')
            self._holdback_lock.acquire()

        with shelve.open(Constants.FOLDER_NAME / str(Constants.EXAMPLE_INSTACE) / f'server{self._id}' / 'db') as db:
            for key, value in read_set.items():
                try:
                    item_version = db[key][0]
                    if item_version > value[1]:
                        logger.warning(f'Client KVS has read an out of date version of item {key}. Current version {item_version}, CKVS version {value[1]}. Transaction needs to be aborted.')
                        self._respond_to_client(requester_address, requester_port, False)
                        return
                except KeyError:
                    pass

            self._last_commited += 1

            for key, value in write_set.items():
                try:
                    next_version = db[key][0] + 1

                    logger.info(f'Server KVS updating version and value of item {key}: ({next_version - 1}, {db[key][1]}) -> ({next_version}, {value})')
                except KeyError:
                    next_version = 0

                    logger.info(f'Server KVS creating item {key}: (0, {value})')

                db[key] = (next_version, value)

        logger.info(f'Server KVS finished commiting the transaction')
        self._respond_to_client(requester_address, requester_port, True)

        logger.info('Server KVS removing transaction from holdback')
        del self._holdback[holdback_key]

        logger.info('Server KVS updating sequence number')
        self._sequence_number += 1

        logger.info('Server KVS notifying all listeners of the sequence number update')
        self._holdback_lock.release()

    def _respond_to_client(self, address, port, commit):
        if commit:
            logger.info('Attempting to send commit message to client')
            message = b'1'
        else:
            logger.info('Attempting to send abort message to client')
            message = b'0'

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                logger.info(f'Server connecting to client -> Address {address}, Port {port}')
                s.connect((address, port))

                logger.info(f'Server sending message -> {message}')
                s.send(message)
        except Exception as e:
            logger.error(f'Server KVS -> An error occurred: {e}')
            return
