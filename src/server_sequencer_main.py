from models.server_sequencer import ServerSequencer
from utils.logger import logger

def main():
    logger.info('Welcome to the server sequencer!')

    ServerSequencer()

if __name__ == '__main__':
    main()
