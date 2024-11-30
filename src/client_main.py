import sys
import code

from src.models.client_key_value_store import ClientKeyValueStore

def main():
    if len(sys.argv) < 2:
        print('Please provide an ID!')
        return

    id = int(sys.argv[1])

    print('Welcome to your client!')
    print('Let us connect you to a KVS.')

    db = ClientKeyValueStore(id)
    print('KVS connected.')

    local_context = locals()
    print('Now you are free to execute any code you want. To call the database, just use the db variable. Enjoy!')

    code.interact(local=local_context)

if __name__ == '__main__':
    main()
