"""Device-local AI connections. Credentials never enter the sync outbox or API responses."""
import ipaddress
import json
import os
from threading import RLock
from urllib.parse import urlsplit, urlunsplit

import httpx
from cryptography.fernet import Fernet, InvalidToken
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .storage import dump, now, uid


class PluginCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str = Field(min_length=1, max_length=80)
    base_url: str = Field(min_length=1, max_length=2048)
    model: str = Field(min_length=1, max_length=160)
    api_key: str = Field(default='', max_length=4096, repr=False)
    enabled: bool = True

    @field_validator('name', 'model')
    @classmethod
    def nonblank(cls, value):
        value = value.strip()
        if not value or any(ord(c) < 32 for c in value):
            raise ValueError('Use nonempty text without control characters')
        return value

    @field_validator('api_key')
    @classmethod
    def key_text(cls, value):
        if value is None:
            return value
        if any(ord(c) < 32 for c in value):
            raise ValueError('API key must not contain control characters')
        return value.strip()

    @field_validator('base_url')
    @classmethod
    def endpoint(cls, value):
        value = value.strip().rstrip('/')
        if any(ord(c) < 33 for c in value) or '\\' in value:
            raise ValueError('Enter a valid API base URL')
        try:
            url = urlsplit(value)
            host = url.hostname
            port = url.port
        except ValueError:
            raise ValueError('Enter a valid API base URL') from None
        if not host or url.username is not None or url.password is not None or url.query or url.fragment:
            raise ValueError('Use a base URL without credentials, query parameters, or fragments')
        local = host.lower() == 'localhost'
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            address = None
        if address:
            local = address.is_loopback
            if not address.is_global and not local:
                raise ValueError('Use a public provider address or an explicit loopback address')
        if url.scheme not in ('https', 'http') or (url.scheme == 'http' and not local):
            raise ValueError('HTTPS is required except for localhost and loopback APIs')
        if port is not None and not 1 <= port <= 65535:
            raise ValueError('Enter a valid port')
        if url.path.endswith('/chat/completions'):
            raise ValueError('Enter the API base URL, without /chat/completions')
        return urlunsplit((url.scheme, url.netloc, url.path, '', ''))


class PluginUpdate(PluginCreate):
    api_key: str | None = Field(default=None, max_length=4096, repr=False)
    clear_api_key: bool = False


class PluginService:
    def __init__(self, store):
        self.store = store
        self.key_path = store.path.parent / '.plugin-key'
        self.key_lock = RLock()
        with store.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS api_plugins(id TEXT PRIMARY KEY, data TEXT NOT NULL)')

    def _cipher(self):
        with self.key_lock:
            return self._load_cipher()

    def _load_cipher(self):
        # A missing key with existing encrypted credentials is an error, never a silent reset.
        if not self.key_path.exists():
            with self.store.connect() as db:
                encrypted = any(json.loads(row[0]).get('secret') for row in db.execute('SELECT data FROM api_plugins'))
            if encrypted:
                raise HTTPException(503, 'The plugin key file is missing. Restore it from your device backup, or clear all saved API keys before adding new ones.')
            try:
                fd = os.open(self.key_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            except FileExistsError:
                pass
            else:
                with os.fdopen(fd, 'wb') as file:
                    file.write(Fernet.generate_key())
        try:
            return Fernet(self.key_path.read_bytes())
        except (OSError, ValueError):
            raise HTTPException(503, 'The local plugin key file could not be read. Restore the backend key file from your device backup.') from None

    def _encrypt(self, key):
        return self._cipher().encrypt(key.encode()).decode() if key else ''

    def _decrypt(self, encrypted):
        try:
            return self._cipher().decrypt(encrypted.encode()).decode() if encrypted else ''
        except (InvalidToken, UnicodeError):
            raise HTTPException(503, 'Saved credentials could not be unlocked. Replace the API key in this connection.') from None

    @staticmethod
    def public(record):
        return {k: record[k] for k in ('id', 'name', 'base_url', 'model', 'enabled', 'is_default',
                                     'last_test', 'created_at', 'updated_at')} | {'has_api_key': bool(record['secret'])}

    def _get(self, db, id):
        row = db.execute('SELECT data FROM api_plugins WHERE id=?', (id,)).fetchone()
        if not row:
            raise HTTPException(404, 'API plugin not found')
        return json.loads(row[0])

    def list(self):
        with self.store.connect() as db:
            return [self.public(json.loads(row[0])) for row in db.execute('SELECT data FROM api_plugins ORDER BY rowid')]

    def create(self, value):
        stamp = now()
        record = {'id': uid(), 'name': value.name, 'base_url': value.base_url, 'model': value.model,
                  'enabled': value.enabled, 'is_default': False, 'secret': self._encrypt(value.api_key),
                  'last_test': None, 'created_at': stamp, 'updated_at': stamp}
        with self.store.connect() as db:
            db.execute('INSERT INTO api_plugins VALUES (?,?)', (record['id'], dump(record)))
        return self.public(record)

    def update(self, id, value):
        new_secret = self._encrypt(value.api_key) if value.api_key else None
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            record = self._get(db, id)
            # An endpoint change never silently forwards the old credential to a new destination.
            secret = '' if value.clear_api_key or record['base_url'] != value.base_url else record['secret']
            if new_secret is not None and not value.clear_api_key:
                secret = new_secret
            changed = (record['base_url'] != value.base_url or record['model'] != value.model or secret != record['secret'])
            record.update(name=value.name, base_url=value.base_url, model=value.model, secret=secret,
                          enabled=value.enabled, is_default=record['is_default'] and value.enabled,
                          updated_at=now(), last_test=None if changed else record['last_test'])
            db.execute('UPDATE api_plugins SET data=? WHERE id=?', (dump(record), id))
        return self.public(record)

    def delete(self, id):
        with self.store.connect() as db:
            self._get(db, id)
            db.execute('DELETE FROM api_plugins WHERE id=?', (id,))
        return {'deleted': True}

    def set_default(self, id):
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            chosen = self._get(db, id)
            if not chosen['enabled']:
                raise HTTPException(409, 'Enable this plugin before making it the default')
            for row in db.execute('SELECT data FROM api_plugins').fetchall():
                record = json.loads(row[0])
                record['is_default'] = record['id'] == id
                db.execute('UPDATE api_plugins SET data=? WHERE id=?', (dump(record), record['id']))
        return self.public(dict(chosen, is_default=True))

    def default_route(self):
        with self.store.connect() as db:
            for row in db.execute('SELECT data FROM api_plugins'):
                record = json.loads(row[0])
                if record['enabled'] and record['is_default']:
                    return ('plugin: ' + record['name'], record['base_url'], record['model'], self._decrypt(record['secret']))
        return None

    def test(self, id):
        with self.store.connect() as db:
            record = self._get(db, id)
        key = self._decrypt(record['secret'])
        outcome = {'ok': False, 'message': 'Could not connect. Check the endpoint and local network.', 'checked_at': now()}
        try:
            response = httpx.post(record['base_url'] + '/chat/completions',
                headers={'Authorization': 'Bearer ' + key} if key else {},
                json={'model': record['model'], 'messages': [{'role': 'user', 'content': 'Reply with OK.'}], 'max_tokens': 16},
                timeout=httpx.Timeout(20, connect=4), follow_redirects=False)
            if response.status_code in (401, 403):
                outcome['message'] = 'Authentication failed. Check the API key and its permissions.'
            elif response.status_code == 429:
                outcome['message'] = 'The provider reported a rate limit or quota limit.'
            elif 300 <= response.status_code < 400:
                outcome['message'] = 'The endpoint redirected the request. Enter its final API base URL.'
            else:
                response.raise_for_status()
                content = response.json()['choices'][0]['message']['content']
                if not isinstance(content, str) or not content.strip():
                    raise ValueError('Empty completion')
                outcome.update(ok=True, message='Connected. The configured model returned a valid chat response.')
        except httpx.HTTPStatusError:
            outcome['message'] = 'The provider rejected the request. Check the base URL, model ID and chat API compatibility.'
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError):
            pass
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            current = self._get(db, id)
            if any(current[k] != record[k] for k in ('base_url', 'model', 'secret')):
                raise HTTPException(409, 'The connection changed during testing. Test its new configuration.')
            current['last_test'] = outcome
            db.execute('UPDATE api_plugins SET data=? WHERE id=?', (dump(current), id))
        return outcome


def plugin_router(service):
    router = APIRouter(prefix='/api/plugins', tags=['API plugins'])

    @router.get('')
    def listing(): return service.list()

    @router.post('', status_code=201)
    def create(value: PluginCreate): return service.create(value)

    @router.put('/{id}')
    def update(id: str, value: PluginUpdate): return service.update(id, value)

    @router.delete('/{id}')
    def delete(id: str): return service.delete(id)

    @router.post('/{id}/default')
    def default(id: str): return service.set_default(id)

    @router.post('/{id}/test')
    def test(id: str): return service.test(id)

    return router
