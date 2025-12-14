def test_add_product(auth_headers):
    response = client.post(
        "/products/",
        json={
            "name": "lait",
            "quantity": 1,
            "expiry_date": "2025-12-30"
        },
        headers=auth_headers
    )
    assert response.status_code == 201
