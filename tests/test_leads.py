import pytest
from fastapi.testclient import TestClient
from backend.app import MAX_BYTES, create_app


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(f'sqlite:///{tmp_path}/test.db')) as c:
        yield c


def lead(email='ravi@example.com', **overrides):
    return dict(name='Ravi', email=email, company='ABC Stores', **overrides)


def upload(client, content):
    return client.post('/leads/import', files={'file': ('leads.csv', content, 'text/csv')})


def test_crud_and_health(client):
    assert client.get('/health').json()['database'] == 'connected'
    response = client.post('/leads', json=lead())
    assert response.status_code == 201
    item = response.json()
    assert item['stage'] == 'new' and item['created_at']
    route = f"/leads/{item['id']}"
    assert client.get(route).json()['email'] == 'ravi@example.com'
    assert client.patch(route, json={'stage': 'qualified'}).json()['stage'] == 'qualified'
    assert client.get('/leads?stage=qualified').json()['total'] == 1
    assert client.delete(route).status_code == 204
    assert client.get(route).status_code == 404


def test_case_insensitive_duplicates_and_update_rollback(client):
    first = client.post('/leads', json=lead()).json()
    assert client.post('/leads', json=lead(' RAVI@example.com ')).status_code == 409
    second = client.post('/leads', json=lead('priya@example.com')).json()
    route = f"/leads/{second['id']}"
    assert client.patch(route, json={'email': first['email'], 'company': 'Changed'}).status_code == 409
    assert client.get(route).json()['company'] == 'ABC Stores'


@pytest.mark.parametrize('change', [{'email': 'invalid'}, {'name': '   '}, {'stage': 'unknown'}, {'extra': 1}])
def test_invalid_create(client, change):
    payload = lead()
    payload.update(change)
    assert client.post('/leads', json=payload).status_code == 422


@pytest.mark.parametrize('change', [{}, {'name': None}, {'stage': None}, {'email': None}])
def test_invalid_patch(client, change):
    item = client.post('/leads', json=lead()).json()
    assert client.patch(f"/leads/{item['id']}", json=change).status_code == 422


def test_search_pagination_and_clear_phone(client):
    item = client.post('/leads', json=lead(phone='123')).json()
    client.post('/leads', json=lead('priya@example.com'))
    assert client.get('/leads?q=ABC&limit=1&offset=1').json()['total'] == 2
    assert len(client.get('/leads?limit=1').json()['items']) == 1
    assert client.get('/leads?q=%25').json()['total'] == 0
    assert client.patch(f"/leads/{item['id']}", json={'phone': None}).json()['phone'] is None
    assert client.get('/leads?limit=101').status_code == 422


def test_csv_partial_success_and_repeat(client):
    body = 'name,email,company\nRavi,ravi@example.com,ABC\nDuplicate,RAVI@example.com,ABC\nBad,bad,ABC\nPriya,priya@example.com,XYZ\n'
    r = upload(client, body)
    assert r.status_code == 200
    assert (r.json()['imported'], r.json()['duplicates'], r.json()['rejected']) == (2, 1, 1)
    assert [x['row'] for x in r.json()['issues']] == [3, 4]
    assert client.get('/leads').json()['total'] == 2
    assert upload(client, body).json()['duplicates'] == 3


@pytest.mark.parametrize('body', ['name,email\nRavi,ravi@example.com', 'name,email,company\n',
    'name,email,company,name\na,b,c,d', b'\xff\xfe'])
def test_bad_csv(client, body):
    assert upload(client, body).status_code == 400
    assert client.get('/leads').json()['total'] == 0


def test_csv_limits_atomic_and_bad_columns(client):
    assert upload(client, b'a' * (MAX_BYTES + 1)).status_code == 413
    body = 'name,email,company\n' + 'Ravi,ravi@example.com,ABC\n' * 1001
    assert upload(client, body).status_code == 413
    assert client.get('/leads').json()['total'] == 0
    r = upload(client, 'name,email,company\nRavi,ravi@example.com\nPriya,priya@example.com,XYZ,extra')
    assert r.json()['rejected'] == 2


def test_records_survive_app_restart(tmp_path):
    url = f'sqlite:///{tmp_path}/persistent.db'
    with TestClient(create_app(url)) as first:
        assert first.post('/leads', json=lead()).status_code == 201
    with TestClient(create_app(url)) as second:
        assert second.get('/leads').json()['items'][0]['email'] == 'ravi@example.com'
