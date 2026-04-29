def get_auth_headers(client):
    response = client.post('/api/auth/login', json={'username': 'admin', 'password': 'admin'})
    token = response.json()['access_token']
    return {'Authorization': f'Bearer {token}'}


def test_vehicles_requires_auth(client):
    response = client.get('/api/vehicles')
    assert response.status_code == 401


def test_create_and_list_vehicle(client):
    headers = get_auth_headers(client)

    create_response = client.post(
        '/api/vehicles',
        json={
            'license_plate': 'ab 1234 cd',
            'status': 'allowed',
            'owner_info': 'John Doe',
        },
        headers=headers,
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created['license_plate'] == 'AB1234CD'
    assert created['status'] == 'allowed'

    list_response = client.get('/api/vehicles?limit=50&offset=0', headers=headers)
    assert list_response.status_code == 200

    payload = list_response.json()
    assert payload['total'] >= 1
    assert any(item['license_plate'] == 'AB1234CD' for item in payload['items'])
