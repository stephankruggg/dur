import sys
import code

from models.client_key_value_store import ClientKeyValueStore
from utils.logger import logger

def main():
    if len(sys.argv) < 2:
        logger.error('Please provide an ID!')
        return

    id = int(sys.argv[1])

    logger.info('Welcome to your client!')
    logger.info('Let us connect you to a KVS.')

    db = ClientKeyValueStore(id)
    logger.info('KVS connected.')

    local_context = locals()
    logger.info('Now you are free to execute any code you want. To call the database, just use the db variable. Enjoy!')

    code.interact(local=local_context)

if __name__ == '__main__':
    main()
