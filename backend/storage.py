import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from uuid import uuid4

def uid(): return str(uuid4())
def now(): return datetime.now(timezone.utc).isoformat()
def dump(value): return json.dumps(value, ensure_ascii=False)

class Store:
    def __init__(self, directory):
        directory.mkdir(parents=True, exist_ok=True)
        self.path = directory / 'state.sqlite3'
        with self.connect() as db:
            db.executescript('''
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS memories(id TEXT PRIMARY KEY, data TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS history(seq INTEGER PRIMARY KEY, entity TEXT, data TEXT);
            CREATE TABLE IF NOT EXISTS operations(seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE, entity TEXT, data TEXT, status TEXT, retries INTEGER DEFAULT 0, next_retry REAL DEFAULT 0, error TEXT);
            CREATE TABLE IF NOT EXISTS conflicts(id TEXT PRIMARY KEY, entity TEXT, data TEXT, resolved INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS chats(id TEXT PRIMARY KEY, title TEXT, created TEXT);
            CREATE TABLE IF NOT EXISTS messages(seq INTEGER PRIMARY KEY AUTOINCREMENT,id TEXT UNIQUE,chat TEXT,role TEXT,content TEXT,created TEXT,metadata TEXT);
            CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT);
            CREATE TABLE IF NOT EXISTS constellation_messages(id TEXT PRIMARY KEY,chat TEXT,role TEXT,content TEXT,created TEXT);
            CREATE TABLE IF NOT EXISTS receipts(id TEXT PRIMARY KEY, request TEXT, response TEXT);
            CREATE TABLE IF NOT EXISTS changes(seq INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT);
            ''')
            db.execute("UPDATE operations SET status='PENDING' WHERE status='SYNCING'")
            db.execute('INSERT OR IGNORE INTO settings VALUES (?,?)', ('device_id', dump(uid())))
    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        try:
            with db: yield db
        finally: db.close()
    def setting(self, key, default=None):
        with self.connect() as db: row = db.execute('SELECT value FROM settings WHERE key=?',(key,)).fetchone()
        return json.loads(row[0]) if row else default
    def set_setting(self,key,value):
        with self.connect() as db: db.execute('INSERT OR REPLACE INTO settings VALUES (?,?)',(key,dump(value)))
    def get(self, id, db=None):
        if db is None:
            with self.connect() as con: return self.get(id,con)
        row=db.execute('SELECT data FROM memories WHERE id=?',(id,)).fetchone()
        return json.loads(row[0]) if row else None
    def all(self):
        with self.connect() as db: return [json.loads(r[0]) for r in db.execute('SELECT data FROM memories')]
    def put(self, db, memory):
        db.execute('INSERT OR REPLACE INTO memories VALUES (?,?)',(memory['memory_id'],dump(memory)))
        db.execute('INSERT INTO history(entity,data) VALUES (?,?)',(memory['memory_id'],dump(memory)))
