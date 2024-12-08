import socket
import traceback
import pickle
import struct
import threading

from utils.constants import Constants
from utils.logger import logger


class ServerDiscoverer:
    def __init__(self):
        self._servers = []

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind((Constants.SERVER_DISCOVERER_ADDRESS, Constants.SERVER_DISCOVERER_PORT))
        self._socket.listen(3)

        self._run()

    def _run(self):
        while True:
            logger.info('Server discoverer listening!')

            connection, address = self._socket.accept()
            logger.info(f'Server discoverer connected to {address}')

            threading.Thread(target=self._handle_connection, args=(connection,)).start()

    def _handle_connection(self, connection):
        with connection:
            try:
                data, _ = connection.recvfrom(4096)
                logger.info(f'Received message {data}')

                message_id, addr, port, sn_addr, sn_port = struct.unpack(Constants.SERVER_DISCOVERER_REQUEST_FORMAT, data)
                addr = socket.inet_ntoa(addr)
                sn_addr = socket.inet_ntoa(sn_addr)

                if message_id == 0:
                    logger.info('Received connect request')
                    self._connect(addr, port, sn_addr, sn_port)
                elif message_id == 1:
                    logger.info('Received disconnect request')
                    self._disconnect(addr, port, sn_addr, sn_port)
                elif message_id == 2:
                    logger.info('Received fetch all servers request')
                    self._fetch_all_servers(connection)
                else:
                    logger.error('Operation not known by server discoverer!')
            except Exception as e:
                logger.error(f'Server discoverer -> An error occurred: {e}')
                traceback.print_exc()

    def _connect(self, address, port, sn_address, sn_port):
        logger.info(f'Server discoverer adding: Address -> {address}, Port -> {port}, SN Address -> {sn_address}, SN Port -> {sn_port}')

        server = (address, port, sn_address, sn_port)
        if server not in self._servers:
            self._servers.append(server)

        logger.info(f'Server discoverer added: Address -> {address}, Port -> {port}, SN Address -> {sn_address}, SN Port -> {sn_port}')

    def _disconnect(self, address, port, sn_address, sn_port):
        logger.info(f'Server discoverer removing: Address -> {address}, Port -> {port}, SN Address -> {sn_address}, SN Port -> {sn_port}')

        server = (address, port, sn_address, sn_port)
        if server in self._servers:
            self._servers.remove(server)

        logger.info(f'Server discoverer removed: Address -> {address}, Port -> {port}, SN Address -> {sn_address}, SN Port -> {sn_port}')

    def _fetch_all_servers(self, connection):
        logger.info('Server discoverer fetching all servers')
        serialized_server_data = pickle.dumps(self._servers)

        logger.info(f'Server discoverer sending servers: {self._servers}')
        connection.sendall(serialized_server_data)

        logger.info('Server discoverer finished sending all servers')
