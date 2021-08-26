import sqlite3, threading, time, os
from typing import Tuple

# storage expires in 1 hour
EXPIRATION = 60 * 60


class KillableThread(threading.Thread):
    ''' https://stackoverflow.com/a/49877671/2327379 '''
    def __init__(self, client, sleep_interval=3600):
        super().__init__()
        self.client = client
        self._interval = sleep_interval
        self._kill = threading.Event()

    def run(self):
        while True:
            cursor = self.client.cursor()
            cursor.execute('SELECT created, ticket FROM storage')
            rows = cursor.fetchall()

            count = 0
            curr_time = int(time.time())
            for created, ticket in rows:
                if curr_time - created > EXPIRATION:
                    cursor.execute(
                        'DELETE FROM storage WHERE ticket=?',
                        (ticket,)
                    )
                    count += 1
            self.client.commit()

            print('Deleted {} expired entries.'.format(count))

            # If no kill signal is set, sleep for the interval,
            # If kill signal comes in while sleeping, immediately
            #  wake up and handle
            is_killed = self._kill.wait(self._interval)
            if is_killed:
                break

    def kill(self):
        self._kill.set()


def initialize_database(filename='sql.db'):
    global client

    # reinitialize
    try: os.remove(filename)
    except FileNotFoundError: pass

    client = sqlite3.connect(filename)

    cursor = client.cursor()
    cursor.execute('''CREATE TABLE storage (
        created INTEGER NOT NULL,
        ticket TEXT PRIMARY KEY NOT NULL,
        username TEXT NOT NULL,
        content BLOB NOT NULL
    )''')
    
    KillableThread(client, sleep_interval=60 * 10).start()


def store_file(ticket: str, username: str, content: bytes):
    cursor = client.cursor()
    cursor.execute(
        'INSERT INTO storage(created, ticket, username, content) VALUES(?,?,?,?)',
        (int(time.time()), ticket, username, content)
    )
    client.commit()


def get_file(ticket: str) -> Tuple[str, bytes]:
    cursor = client.cursor()
    cursor.execute(
        'SELECT username, content FROM storage WHERE ticket=?',
        (ticket,)
    )
    rows = cursor.fetchall()
    if len(rows) != 1:
        raise ValueError
    username, content = rows[0]

    cursor.execute(
        'DELETE FROM storage WHERE ticket=?',
        (ticket,)
    )
    client.commit()
    return username, content
