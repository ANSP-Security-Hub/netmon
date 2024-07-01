#!./venv/bin/python3
import sys
import time

from status_db import StatusDB
from syslog_sender import send_syslog_json_message
from dotenv import load_dotenv
import os

load_dotenv()

REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL"))


def main():
    db = StatusDB()
    last_start_time = int(time.time())
    while True:
        try:
            db.update_connections()
        except Exception as e:
            print(f"------ Error: {e}", file=sys.stderr)
        status = db.get_db_status()
        print(f"Active connections: {status['active_connections']}", file=sys.stderr)
        print(f"Idle connections: {status['idle_connections']}", file=sys.stderr)
        print(f"Closed connections: {status['closed_connections']}", file=sys.stderr)
        connections = db.get_connections()
        for conn in connections['active_connections']:
            conn['status'] = 'active'
            send_syslog_json_message(conn)
        for conn in connections['idle_connections']:
            conn['status'] = 'idle'
            send_syslog_json_message(conn)
        for conn in connections['closed_connections']:
            conn['status'] = 'closed'
            send_syslog_json_message(conn)
        while True:
            time_remaining = REFRESH_INTERVAL - (int(time.time()) - last_start_time)
            if time_remaining <= 0:
                last_start_time = int(time.time())
                break
            print(f"Next update in {time_remaining} seconds        ", file=sys.stderr, end='\r')
            time.sleep(0.95)


if __name__ == '__main__':
    main()

