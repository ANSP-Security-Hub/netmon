import json
import time

from connection import Connection
from flow2conn import get_last_connections
from dotenv import load_dotenv
import os

load_dotenv()


class StatusDB:
    # store active connections key: id: int, value: Connection
    active_connections: dict[int, Connection] = {}
    idle_connections: dict[int, Connection] = {}
    closed_connections: dict[int, Connection] = {}

    REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL"))
    CONNECTION_TIMEOUT_DURATION = int(os.getenv("CONNECTION_TIMEOUT_DURATION"))
    MAX_ACTIVE_CONNECTIONS = int(os.getenv("MAX_ACTIVE_CONNECTIONS"))
    ENRICH_BATCH_LIMIT = int(os.getenv("ENRICH_BATCH_LIMIT"))

    _last_update = 0

    def __init__(self):
        pass

    @classmethod
    def update_connections(cls):
        if time.time() - cls._last_update < cls.REFRESH_INTERVAL * 0.9:
            raise ValueError("Connections were updated too recently. Please wait a for a while before updating again.")
        cls._last_update = time.time()
        new_connections = get_last_connections(cls.REFRESH_INTERVAL, cls.MAX_ACTIVE_CONNECTIONS)
        active_connections = {}
        enrich_count = 0
        # update active connections
        for conn in new_connections:
            if conn.get_id() in cls.active_connections:
                cls.active_connections[conn.get_id()].merge(conn)
                active_connections[conn.get_id()] = cls.active_connections.pop(conn.get_id())
            elif conn.get_id() in cls.idle_connections:
                cls.idle_connections[conn.get_id()].merge(conn)
                active_connections[conn.get_id()] = cls.idle_connections.pop(conn.get_id())
            else:
                if enrich_count < cls.ENRICH_BATCH_LIMIT:
                    enrich_count += 1
                    conn.enrich()
                active_connections[conn.get_id()] = conn

        # update idle connections
        for conn in list(cls.idle_connections.values()):
            if time.time() - conn.last_seen > cls.CONNECTION_TIMEOUT_DURATION:
                conn.finished = True
                cls.closed_connections[conn.get_id()] = cls.idle_connections.pop(conn.get_id())

        # all remaining connections are idle
        cls.idle_connections.update(cls.active_connections)
        cls.active_connections = active_connections

    @classmethod
    def get_db_status(cls):
        return {
            "active_connections": len(cls.active_connections),
            "idle_connections": len(cls.idle_connections),
            "closed_connections": len(cls.closed_connections)
        }

    @classmethod
    def get_connections(cls):
        result = {
            "active_connections": [conn.as_dict() for conn in cls.active_connections.values()],
            "idle_connections": [conn.as_dict() for conn in cls.idle_connections.values()],
            "closed_connections": [conn.as_dict() for conn in cls.closed_connections.values()]
        }

        cls.closed_connections.clear()
        return result


if __name__ == '__main__':
    db = StatusDB()
    for _ in range(100):
        db.update_connections()
        connections = db.get_connections()
        for conn in connections['active_connections']:
            conn['last_seen'] = time.ctime(conn['last_seen'])
            conn['first_seen'] = time.ctime(conn['first_seen'])
        for conn in connections['idle_connections']:
            conn['last_seen'] = time.ctime(conn['last_seen'])
            conn['first_seen'] = time.ctime(conn['first_seen'])
        for conn in connections['closed_connections']:
            conn['last_seen'] = time.ctime(conn['last_seen'])
            conn['first_seen'] = time.ctime(conn['first_seen'])
        print(json.dumps(connections, indent=4))
        for sec in range(StatusDB.REFRESH_INTERVAL):
            time.sleep(1)
            print(f"Next update in {StatusDB.REFRESH_INTERVAL - sec} seconds ", end='\r')
