import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home_route(client):
    """Test home route returns correct status"""
    response = client.get('/')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'Gym AI API is running!'

def test_analyse_no_image(client):
    """Test analyse returns 400 when no image sent"""
    response = client.post('/analyse',
                           json={},
                           content_type='application/json')
    assert response.status_code == 400
    data = response.get_json()
    assert data['detected'] == False

def test_analyse_missing_body(client):
    """Test analyse handles completely empty body"""
    response = client.post('/analyse',
                           content_type='application/json')
    assert response.status_code in [400, 500]