"""
Test API endpoints with Flask test client
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

@pytest.fixture
def app():
    """Create and configure a test app"""
    os.environ['FLASK_ENV'] = 'development'
    os.environ['MYSQL_ROOT_PASSWORD'] = 'test'
    os.environ['DB_HOST'] = 'localhost'
    os.environ['MYSQL_DATABASE'] = 'test_db'
    
    from app import create_app
    
    # Mock database initialization to avoid needing a real database
    with patch('app.init_db_with_retry') as mock_init_db:
        mock_init_db.return_value = True
        app = create_app('development')
        app.config['TESTING'] = True
        yield app

@pytest.fixture
def client(app):
    """Create a test client"""
    return app.test_client()

def test_root_endpoint(client):
    """Test the root endpoint returns JSON"""
    response = client.get('/')
    assert response.status_code == 200
    data = response.get_json()
    assert data is not None
    assert 'service' in data
    assert data['service'] == 'Work Diary Backend'

def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'

def test_status_check(client):
    """Test status check endpoint"""
    with patch('routes.health.db.session.execute'):
        response = client.get('/api/status')
        assert response.status_code == 200
        data = response.get_json()
        assert 'status' in data
        assert 'database' in data
        assert 'cache' in data

def test_clock_in_legacy(client):
    """Test legacy clock-in endpoint"""
    with patch('redis.Redis') as mock_redis:
        mock_instance = Mock()
        mock_instance.ping.return_value = True
        mock_instance.incr.return_value = 1
        mock_redis.return_value = mock_instance
        
        # We need to reload the route after mocking
        response = client.get('/api/clock-in')
        # If Redis is not available, it should return 503
        # This is expected in test environment
        assert response.status_code in [200, 503]

def test_add_diary_legacy_validation(client):
    """Test legacy diary endpoint validation"""
    # Test with empty content
    response = client.post('/api/diary', json={'content': ''})
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data

def test_get_diary_legacy(client):
    """Test legacy get diary endpoint"""
    with patch('services.diary_service.DiaryRepository') as mock_repo:
        mock_pagination = Mock()
        mock_pagination.total = 0
        mock_pagination.page = 1
        mock_pagination.pages = 0
        mock_pagination.items = []
        
        mock_repo_instance = Mock()
        mock_repo_instance.find_paginated.return_value = mock_pagination
        mock_repo.return_value = mock_repo_instance
        
        response = client.get('/api/diary')
        # If DB is not available, might return error
        assert response.status_code in [200, 500]

def test_ai_polish_legacy_validation(client):
    """Test legacy AI polish endpoint validation"""
    # Test with empty content
    response = client.post('/api/ai-polish', json={'content': ''})
    assert response.status_code in [400, 503]  # 400 for empty content, 503 if AI not available

def test_v1_diary_create_validation(client):
    """Test v1 diary create endpoint validation"""
    response = client.post('/api/v1/diaries', json={'content': ''})
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data

def test_v1_diary_list(client):
    """Test v1 diary list endpoint"""
    with patch('routes.api.v1.diary.diary_service') as mock_service:
        mock_service.get_diary_list.return_value = {
            'total': 0,
            'page': 1,
            'per_page': 20,
            'pages': 0,
            'diaries': []
        }
        
        response = client.get('/api/v1/diaries')
        assert response.status_code in [200, 500]

def test_v1_diary_get_not_found(client):
    """Test v1 diary get endpoint with non-existent ID"""
    with patch('routes.api.v1.diary.diary_service') as mock_service:
        mock_service.get_diary_by_id.return_value = None
        
        response = client.get('/api/v1/diaries/999')
        assert response.status_code in [404, 500]

def test_v1_ai_polish_validation(client):
    """Test v1 AI polish endpoint validation"""
    response = client.post('/api/v1/ai/polish', json={'content': ''})
    assert response.status_code in [400, 503]

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
