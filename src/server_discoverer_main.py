from utils.logger import logger
from models.server_discoverer import ServerDiscoverer

def main():
    logger.info('Welcome to the server discoverer!')

    ServerDiscoverer()

if __name__ == '__main__':
    main()
