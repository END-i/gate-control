def test_login_success(client):
    response = client.post('/api/auth/login', json={'username': 'admin', 'password': 'admin'})

    assert response.status_code == 200
    data = response.json()
    assert 'access_token' in data
    assert data['token_type'] == 'bearer'


def test_login_invalid_credentials(client):
    response = client.post('/api/auth/login', json={'username': 'admin', 'password': 'wrong'})

    assert response.status_code == 401
    assert response.json()['detail'] == 'Invalid credentials'
