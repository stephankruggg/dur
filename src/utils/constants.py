from pathlib import Path

class Constants:
    EXAMPLE_INSTACE = 1
    FOLDER_NAME = Path('examples')

    SERVER_KEY_VALUE_STORE_ADDRESS = '127.0.0.1'
    SERVER_KEY_VALUE_STORE_BASE_PORT = 5000

    SERVER_DISCOVERER_ADDRESS = '127.0.0.1'
    SERVER_DISCOVERER_PORT = 5100

    SERVER_SEQUENCER_ADDRESS = '127.0.0.1'
    SERVER_SEQUENCER_PORT = 5200

    SERVER_KEY_VALUE_STORE_SN_ADDRESS = '127.0.0.1'
    SERVER_KEY_VALUE_STORE_SN_PORT = 5300

    # Request type (1B) -> 0 - Connect; 1 - Disconnect; 2 - Fetch all servers; Requester address (4B String), Requester port (2B), Sequence number listener address (4B String), Sequence number listener port (2B)
    SERVER_DISCOVERER_REQUEST_FORMAT = '!B4sH4sH'

    # Request type (1B) -> 0 - Read, Variable name (255B String)
    READ_REQUEST_FORMAT = '!B255s'

    # Request type (1B) -> 1 - Deliver, Requester address (4B String), Requester port (2B), Client transaction ID (4B Integer)
    DELIVER_REQUEST_INITIAL_FORMAT = '!B4sHI'

    # Variable version (4B Integer)
    READ_RESPONSE_INITIAL_FORMAT = '!I'

    # Requester address (4B String), Requester port (2B), Requester transaction ID (4B Integer), Sequence number (4B)
    SERVER_SEQUENCER_FORMAT = '!4sHII'
