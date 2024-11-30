from pathlib import Path

class Constants:
    EXAMPLE_INSTACE = 1
    FOLDER_NAME = Path('examples')

    SERVER_DISCOVERER_ADDRESS = '127.0.0.1'
    SERVER_DISCOVERER_PORT = 5100

    # Request type (1B) -> 0 - Connect; 1 - Disconnect; 2 - Fetch all servers; Requester address (4B String), Requester port (2B)
    SERVER_DISCOVERER_REQUEST_FORMAT = '!B4sH'

    SERVER_KEY_VALUE_STORE_ADDRESS = '127.0.0.1'
    SERVER_KEY_VALUE_STORE_BASE_PORT = 5000

    # Request type (1B) -> 0 - Read, Variable name (255B String)
    READ_REQUEST_FORMAT = '!B255s'

    # Request type (1B) -> 1 - Deliver, Requester address (4B String), Requester port (2B)
    DELIVER_REQUEST_INITIAL_FORMAT = '!B4sH'

    # Variable version (4B Integer)
    READ_RESPONSE_INITIAL_FORMAT = '!I'
