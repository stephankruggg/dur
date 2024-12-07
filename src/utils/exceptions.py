class ServersNotFoundException(Exception):
    def __init__(self) -> None:
        msg = 'No servers found'
        super().__init__(msg)
