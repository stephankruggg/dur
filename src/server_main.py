import os
import sys

from models.server_key_value_store import ServerKeyValueStore
from utils.exceptions import ServerDiscovererNotFoundException
from utils.logger import logger

def main():
    if len(sys.argv) < 2:
        logger.error('Please provide an ID!')
        return

    id = int(sys.argv[1])

    logger.info('Welcome to your server!')
    logger.info('Your KVS will begin running promptly.')
    logger.info(f'Your environment will be created in a server {id} folder. Enjoy!')

    try:
        ServerKeyValueStore(id)
    except ServerDiscovererNotFoundException as e:
        logger.error(e)

    os._exit(0)

if __name__ == '__main__':
    main()
