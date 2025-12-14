def test_add_product(client, auth_headers):
    response = client.post(
        "/products/",
        json={
            "name": "Lait",
            "quantity": 1,
            "expiry_date": "2025-12-31"
        },
        headers=auth_headers
    )
    print(response.json())

    assert response.status_code in [200, 201]
