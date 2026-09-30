"""API plugin lifecycle and routing checks; no model downloads or live API calls."""

import json

import httpx
import pytest
from fastapi.testclient import TestClient

from backend.config import Settings


@pytest.fixture
def client(tmp_path):
    from backend.main import create_app

    app = create_app(Settings(
        _env_file=None,
        data_dir=tmp_path / 'device',
        cloud_url='',
        cloud_model_url='',
        cloud_model='',
        cloud_api_key='',
        local_model_url='http://127.0.0.1:11434/v1',
        local_model='offline-model',
    ), enable_worker=False)
    # Plugin management doesn't require startup of the vector repository.
    result = TestClient(app)
    yield result
    result.close()
    app.state.sync.client.close()


def plugin_body(**overrides):
    return {
        'name': 'Example API',
        'base_url': 'https://models.example/v1',
        'model': 'example-model',
        'api_key': 'test-plugin-secret',
        'enabled': True,
        **overrides,
    }


def add_plugin(client, **overrides):
    response = client.post('/api/plugins', json=plugin_body(**overrides))
    assert response.status_code == 201, response.text
    return response.json()


def edit_plugin(client, plugin, **overrides):
    body = plugin_body(api_key='', **overrides)
    return client.put('/api/plugins/' + plugin['id'], json=body)


def capture_requests(monkeypatch, fail_plugin=False, content='API answer'):
    calls = []

    def post(url, **kwargs):
        calls.append((url, kwargs))
        if fail_plugin and url.startswith('https://models.example'):
            raise httpx.ConnectError('Endpoint unavailable')
        return httpx.Response(
            200,
            json={'choices': [{'message': {'content': content}}]},
            request=httpx.Request('POST', url),
        )

    monkeypatch.setattr(httpx, 'post', post)
    return calls


def test_plugin_persists_without_returning_key(client):
    from backend.plugins import PluginService

    plugin = add_plugin(client)
    assert plugin['name'] == 'Example API'
    assert plugin['has_api_key'] is True
    assert plugin['is_default'] is False
    assert plugin['last_test'] is None
    assert plugin['created_at'] and plugin['updated_at']
    assert 'api_key' not in plugin
    assert 'test-plugin-secret' not in json.dumps(plugin)
    for path in client.app.state.models.settings.data_dir.glob('state.sqlite3*'):
        assert b'test-plugin-secret' not in path.read_bytes()
    # A new application/service instance must observe the same saved connection.
    from backend.main import create_app
    app = create_app(client.app.state.models.settings, enable_worker=False)
    reopened = TestClient(app)
    try:
        records = reopened.get('/api/plugins').json()
        assert records == [plugin]
        assert 'test-plugin-secret' not in json.dumps(records)
        assert isinstance(app.state.models.plugins, PluginService)
    finally:
        reopened.close()
        app.state.sync.client.close()


def test_default_plugin_is_explicit_and_uses_saved_model_and_key(client, monkeypatch):
    calls = capture_requests(monkeypatch)
    plugin = add_plugin(client)
    models = client.app.state.models
    models.complete([{'role': 'user', 'content': 'Before activation'}])
    assert calls[-1][0] == 'http://127.0.0.1:11434/v1/chat/completions'
    assert client.post('/api/plugins/' + plugin['id'] + '/default').status_code == 200
    answer, route = models.complete([{'role': 'user', 'content': 'Hello'}])
    url, request = calls[-1]
    assert answer == 'API answer' and route != 'local'
    assert url == 'https://models.example/v1/chat/completions'
    assert request['json']['model'] == 'example-model'
    assert request['headers']['Authorization'] == 'Bearer test-plugin-secret'


def test_only_one_default_and_disabled_plugin_cannot_be_default(client):
    first = add_plugin(client)
    second = add_plugin(client, name='Second API')
    assert client.post('/api/plugins/' + first['id'] + '/default').status_code == 200
    assert client.post('/api/plugins/' + second['id'] + '/default').status_code == 200
    records = client.get('/api/plugins').json()
    assert [item['id'] for item in records if item['is_default']] == [second['id']]
    response = edit_plugin(client, second, enabled=False)
    assert response.status_code == 200
    assert response.json()['is_default'] is False
    assert client.post('/api/plugins/' + second['id'] + '/default').status_code in (409, 422)
    assert not any(item['is_default'] for item in client.get('/api/plugins').json())


def test_blank_key_edit_preserves_existing_key(client, monkeypatch):
    calls = capture_requests(monkeypatch)
    plugin = add_plugin(client)
    assert client.post('/api/plugins/' + plugin['id'] + '/default').status_code == 200
    response = edit_plugin(client, plugin, name='Renamed API')
    assert response.status_code == 200 and response.json()['has_api_key']
    client.app.state.models.complete([{'role': 'user', 'content': 'Hello'}])
    assert calls[-1][1]['headers']['Authorization'] == 'Bearer test-plugin-secret'
    assert 'test-plugin-secret' not in response.text


def test_explicit_key_removal_and_replacement(client, monkeypatch):
    calls = capture_requests(monkeypatch)
    plugin = add_plugin(client)
    client.post('/api/plugins/' + plugin['id'] + '/default')
    response = edit_plugin(client, plugin, clear_api_key=True)
    assert response.status_code == 200 and not response.json()['has_api_key']
    client.app.state.models.complete([{'role': 'user', 'content': 'No key'}])
    assert 'Authorization' not in calls[-1][1]['headers']
    response = client.put('/api/plugins/' + plugin['id'], json=plugin_body(api_key='replacement-secret'))
    assert response.status_code == 200 and response.json()['has_api_key']
    client.app.state.models.complete([{'role': 'user', 'content': 'New key'}])
    assert calls[-1][1]['headers']['Authorization'] == 'Bearer replacement-secret'
    assert 'replacement-secret' not in response.text


def test_changing_endpoint_cannot_forward_previous_credentials(client, monkeypatch):
    calls = capture_requests(monkeypatch)
    plugin = add_plugin(client)
    client.post('/api/plugins/' + plugin['id'] + '/default')
    response = edit_plugin(client, plugin, base_url='https://different.example/v1')
    assert response.status_code == 200 and not response.json()['has_api_key']
    client.app.state.models.complete([{'role': 'user', 'content': 'Hello'}])
    assert calls[-1][0] == 'https://different.example/v1/chat/completions'
    assert 'Authorization' not in calls[-1][1]['headers']


def test_plugin_failure_falls_back_to_local(client, monkeypatch):
    calls = capture_requests(monkeypatch, fail_plugin=True)
    plugin = add_plugin(client)
    client.post('/api/plugins/' + plugin['id'] + '/default')
    models = client.app.state.models
    models.settings.cloud_model_url = 'https://environment.example/v1'
    models.settings.cloud_api_key = 'environment-secret'
    models.settings.cloud_model = 'environment-model'
    result = models.complete([{'role': 'user', 'content': 'Hello'}])
    assert result == ('API answer', 'local')
    assert [url for url, _ in calls] == [
        'https://models.example/v1/chat/completions',
        'http://127.0.0.1:11434/v1/chat/completions',
    ]


def test_force_local_bypasses_plugin_and_environment_provider(client, monkeypatch):
    calls = capture_requests(monkeypatch)
    plugin = add_plugin(client)
    client.post('/api/plugins/' + plugin['id'] + '/default')
    models = client.app.state.models
    models.settings.cloud_model_url = 'https://environment.example/v1'
    models.settings.cloud_api_key = 'environment-secret'
    models.settings.cloud_model = 'environment-model'
    assert models.complete([{'role': 'user', 'content': 'Private memory'}], force_local=True)[1] == 'local'
    assert len(calls) == 1
    assert calls[0][0] == 'http://127.0.0.1:11434/v1/chat/completions'
    assert 'Authorization' not in calls[0][1]['headers']


def test_delete_removes_connection_from_routing(client, monkeypatch):
    calls = capture_requests(monkeypatch)
    plugin = add_plugin(client)
    client.post('/api/plugins/' + plugin['id'] + '/default')
    assert client.delete('/api/plugins/' + plugin['id']).status_code in (200, 204)
    assert client.get('/api/plugins').json() == []
    assert client.post('/api/plugins/' + plugin['id'] + '/default').status_code == 404
    assert client.post('/api/plugins/' + plugin['id'] + '/test').status_code == 404
    client.app.state.models.complete([{'role': 'user', 'content': 'Hello'}])
    assert calls[-1][0] == 'http://127.0.0.1:11434/v1/chat/completions'


def test_connection_test_sends_only_synthetic_message_and_persists_result(client, monkeypatch):
    calls = capture_requests(monkeypatch)
    plugin = add_plugin(client)
    response = client.post('/api/plugins/' + plugin['id'] + '/test')
    assert response.status_code == 200
    assert len(calls) == 1
    url, request = calls[0]
    assert url == 'https://models.example/v1/chat/completions'
    assert request['json']['model'] == 'example-model'
    assert 0 < request['json']['max_tokens'] <= 32
    assert all(len(item['content']) < 200 for item in request['json']['messages'])
    saved = client.get('/api/plugins').json()[0]
    assert saved['last_test']['ok'] is True
    assert saved['last_test']['message'] and saved['last_test']['checked_at']
    assert not saved['is_default']
    assert 'test-plugin-secret' not in response.text


def test_failed_connection_test_does_not_expose_provider_response_or_secret(client, monkeypatch):
    def post(url, **kwargs):
        return httpx.Response(
            401,
            json={'error': {'message': 'Key test-plugin-secret rejected'}},
            request=httpx.Request('POST', url),
        )

    monkeypatch.setattr(httpx, 'post', post)
    plugin = add_plugin(client)
    response = client.post('/api/plugins/' + plugin['id'] + '/test')
    assert response.status_code == 200
    saved = client.get('/api/plugins').json()[0]
    assert saved['last_test']['ok'] is False
    assert 'test-plugin-secret' not in response.text
    assert 'test-plugin-secret' not in json.dumps(saved)


@pytest.mark.parametrize('base_url', [
    'http://public.example/v1',
    'https://user:password@models.example/v1',
    'https://models.example/v1?secret=key',
    'https://models.example/v1#fragment',
    'file:///etc/passwd',
    'http://169.254.169.254/latest/meta-data',
    'https://169.254.169.254/v1',
    'https://192.168.1.5/v1',
    'https://10.0.0.2/v1',
    'https://[fd00::1]/v1',
])
def test_rejects_unsafe_endpoint_urls(client, base_url):
    response = client.post('/api/plugins', json=plugin_body(base_url=base_url))
    assert response.status_code == 422
    assert client.get('/api/plugins').json() == []


@pytest.mark.parametrize('base_url', [
    'http://127.0.0.1:11434/v1',
    'http://[::1]:8081/v1',
    'https://models.example/v1',
])
def test_accepts_https_and_literal_loopback_endpoints(client, base_url):
    plugin = add_plugin(client, base_url=base_url, api_key='')
    assert plugin['base_url'] == base_url
    assert plugin['has_api_key'] is False


def test_cross_origin_plugin_changes_are_blocked(client):
    response = client.post('/api/plugins', json=plugin_body(), headers={'Origin': 'https://attacker.example'})
    assert response.status_code == 403
    assert client.get('/api/plugins').json() == []


def test_missing_vault_falls_back_locally_and_clear_all_keys_allows_recovery(client, monkeypatch):
    calls = capture_requests(monkeypatch)
    first = add_plugin(client)
    second = add_plugin(client, name='Second API')
    client.post('/api/plugins/' + first['id'] + '/default')
    models = client.app.state.models
    models.settings.cloud_model_url = 'https://environment.example/v1'
    models.settings.cloud_api_key = 'environment-secret'
    models.settings.cloud_model = 'environment-model'
    key_path = models.settings.data_dir / '.plugin-key'
    key_path.unlink()
    assert models.complete([{'role': 'user', 'content': 'Private context'}])[1] == 'local'
    assert len(calls) == 1 and calls[0][0].startswith('http://127.0.0.1:')
    response = client.post('/api/plugins/' + first['id'] + '/test')
    assert response.status_code == 503
    assert not key_path.exists()
    assert 'test-plugin-secret' not in response.text
    for plugin in (first, second):
        response = edit_plugin(client, plugin, clear_api_key=True)
        assert response.status_code == 200 and not response.json()['has_api_key']
    response = client.put('/api/plugins/' + first['id'], json=plugin_body(api_key='recovered-secret'))
    assert response.status_code == 200 and response.json()['has_api_key']
    assert key_path.exists()
    models.complete([{'role': 'user', 'content': 'Recovered'}])
    assert calls[-1][1]['headers']['Authorization'] == 'Bearer recovered-secret'


def test_validation_errors_do_not_echo_keys(client):
    response = client.post('/api/plugins', json=plugin_body(api_key='test-secret\ninvalid-header'))
    assert response.status_code == 422
    assert 'test-secret' not in response.text
    assert 'invalid-header' not in response.text


@pytest.mark.parametrize('provider_body', [
    {'choices': []},
    {'choices': [{'message': {'content': None}}]},
    {'choices': [{'message': {'content': ' '}}]},
])
def test_malformed_plugin_response_falls_back_locally(client, monkeypatch, provider_body):
    calls = []

    def post(url, **kwargs):
        calls.append(url)
        body = provider_body if url.startswith('https://models.example') else {'choices': [{'message': {'content': 'Offline answer'}}]}
        return httpx.Response(200, json=body, request=httpx.Request('POST', url))

    monkeypatch.setattr(httpx, 'post', post)
    plugin = add_plugin(client)
    client.post('/api/plugins/' + plugin['id'] + '/default')
    assert client.app.state.models.complete([{'role': 'user', 'content': 'Hello'}]) == ('Offline answer', 'local')
    assert len(calls) == 2 and calls[-1].startswith('http://127.0.0.1:')


def test_edit_invalidates_old_connection_result(client, monkeypatch):
    capture_requests(monkeypatch)
    plugin = add_plugin(client)
    assert client.post('/api/plugins/' + plugin['id'] + '/test').json()['ok']
    response = edit_plugin(client, plugin, model='different-model')
    assert response.status_code == 200 and response.json()['last_test'] is None


def test_connection_changed_during_test_cannot_receive_stale_success(client, monkeypatch):
    plugin = add_plugin(client)

    def post(url, **kwargs):
        response = edit_plugin(client, plugin, model='changed-during-test')
        assert response.status_code == 200
        return httpx.Response(200, json={'choices': [{'message': {'content': 'OK'}}]}, request=httpx.Request('POST', url))

    monkeypatch.setattr(httpx, 'post', post)
    response = client.post('/api/plugins/' + plugin['id'] + '/test')
    assert response.status_code == 409
    saved = client.get('/api/plugins').json()[0]
    assert saved['model'] == 'changed-during-test' and saved['last_test'] is None
