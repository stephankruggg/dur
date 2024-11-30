import sys
import code

from src.models.server_key_value_store import ServerKeyValueStore

def main():
    if len(sys.argv) < 2:
        print('Please provide an ID!')
        return

    id = int(sys.argv[1])

    print('Welcome to your server!')
    print('Your KVS will begin running promptly.')
    print(f'Your environment will be created in a server {id} folder. Enjoy!')

    db = ServerKeyValueStore(id)

if __name__ == '__main__':
    main()
