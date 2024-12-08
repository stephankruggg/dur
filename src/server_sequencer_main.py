from models.server_sequencer import ServerSequencer
from utils.exceptions import ServerDiscovererNotFoundException, ServersNotFoundException
from utils.logger import logger

def main():
    logger.info('Welcome to the server sequencer!')

    try:
        ServerSequencer()
    except ServerDiscovererNotFoundException as e:
        logger.error(e)
    except ServersNotFoundException as e:
        logger.error(e)

if __name__ == '__main__':
    main()
