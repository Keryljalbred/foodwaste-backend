def test_login_user():
    response = client.post(
        "/users/login",
        data={
            "username": "user@test.com",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
