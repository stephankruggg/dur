import socket
import traceback
import pickle
import struct

from src.utils.constants import Constants

class ServerDiscoverer:
    def __init__(self):
        self._servers = []

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind((Constants.SERVER_DISCOVERER_ADDRESS, Constants.SERVER_DISCOVERER_PORT))
        self._socket.listen(3)

        self._run()

    def _run(self):
        while True:
            print('Server discoverer listening!')

            connection, address = self._socket.accept()
            print(f'Server discoverer connected to {address}')

            # To do: Transform this into separate thread
            with connection:
                try:
                    data, _ = connection.recvfrom(4096)

                    message_id, addr, port = struct.unpack(Constants.SERVER_DISCOVERER_REQUEST_FORMAT, data)
                    addr = socket.inet_ntoa(addr)

                    if message_id == 0:
                        self._connect(addr, port)
                    elif message_id == 1:
                        # To do: implement disconnect on servers
                        self._disconnect(addr, port)
                    elif message_id == 2:
                        self._fetch_all_servers(connection)
                    else:
                        print('Operation not known by server discoverer!')
                except Exception as e:
                    print(f'Server discoverer -> An error occurred: {e}')
                    traceback.print_exc()

    def _connect(self, address, port):
        print(f'Server discoverer adding: Address -> {address}, Port -> {port}')

        server = (address, port)
        if server not in self._servers:
            self._servers.append(server)

        print(f'Server discoverer added: Address -> {address}, Port -> {port}')

    def _disconnect(self, address, port):
        print(f'Server discoverer removing: Address -> {address}, Port -> {port}')

        server = (address, port)
        if server in self._servers:
            self._servers.remove(server)

        print(f'Server discoverer removed: Address -> {address}, Port -> {port}')

    def _fetch_all_servers(self, connection):
        print('Server discoverer fetching all servers')
        serialized_server_data = pickle.dumps(self._servers)

        print(self._servers)
        print(serialized_server_data)
        print(f'Server discoverer sending servers: {self._servers}')
        connection.sendall(serialized_server_data)

        print('Server discoverers finished sending all servers')

