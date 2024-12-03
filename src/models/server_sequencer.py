import socket
import struct
import pickle
import traceback

from utils.constants import Constants

class ServerSequencer:
    def __init__(self):
        self._sequence_number = 0

        self._address = Constants.SERVER_SEQUENCER_ADDRESS
        self._port = Constants.SERVER_SEQUENCER_PORT

        self._connect_to_server_discoverer()

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind((self._address, self._port))
        self._socket.listen(3)

        self._run()

    def _connect_to_server_discoverer(self):
        print('Attempting to get known by the server discoverer.')

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((Constants.SERVER_DISCOVERER_ADDRESS, Constants.SERVER_DISCOVERER_PORT))

            message = struct.pack(Constants.SERVER_DISCOVERER_REQUEST_FORMAT, 0, socket.inet_aton(self._address), self._port, socket.inet_aton(self._address), self._port)

            s.send(message)

            print('Server now known!')

    def _run(self):
        while True:
            print('Server sequencer listening...')

            connection, _ = self._socket.accept()

            try:
                data = connection.recv(4096)

                self._send_sequence_number(data)

                self._sequence_number += 1
            except Exception as e:
                print(f'Server KVS -> An error occurred: {e}')
                traceback.print_exc()

    def _send_sequence_number(self, data):
        if data[0] != 1:
            return

        _, requester_address, requester_port, message_id = struct.unpack(Constants.DELIVER_REQUEST_INITIAL_FORMAT, data[:11])

        message = struct.pack(Constants.SERVER_SEQUENCER_FORMAT, requester_address, requester_port, message_id, self._sequence_number)

        for server_address, server_port, server_sn_address, server_sn_port in self._fetch_all_servers():
            if server_address == self._address and server_port == self._port:
                continue

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                print(f'Server sequencer sending sequence number to server -> Sequence number {self._sequence_number}, Address {server_sn_address}, Port {server_sn_port}')
                s.connect((server_sn_address, server_sn_port))

                s.send(message)

    def _fetch_all_servers(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((Constants.SERVER_DISCOVERER_ADDRESS, Constants.SERVER_DISCOVERER_PORT))

            addr, port = s.getsockname()
            message = struct.pack(Constants.SERVER_DISCOVERER_REQUEST_FORMAT, 2, socket.inet_aton(addr), port, socket.inet_aton(addr), port)

            s.send(message)

            response = b''

            while True:
                packet = s.recv(4096)

                if not packet:
                    break

                response += packet

        return pickle.loads(response)
