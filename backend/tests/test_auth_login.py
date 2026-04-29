def test_login_success(client):
    response = client.post('/api/auth/login', json={'username': 'admin', 'password': 'admin'})

    assert response.status_code == 200
    data = response.json()
    assert 'access_token' in data
    assert data['token_type'] == 'bearer'
    assert data['role'] == 'admin'


def test_login_invalid_credentials(client):
    response = client.post('/api/auth/login', json={'username': 'admin', 'password': 'wrong'})

    assert response.status_code == 401
    assert response.json()['detail'] == 'Invalid credentials'


def test_auth_me_requires_token(client):
    response = client.get('/api/auth/me')
    assert response.status_code == 401


def test_auth_me_success(client):
    login = client.post('/api/auth/login', json={'username': 'admin', 'password': 'admin'})
    token = login.json()['access_token']

    response = client.get('/api/auth/me', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    assert response.json()['username'] == 'admin'
    assert response.json()['role'] == 'admin'
