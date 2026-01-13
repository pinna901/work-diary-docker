"""
Test clock-in functionality
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

@pytest.fixture
def mock_redis():
    """Create a mock Redis client"""
    redis_mock = Mock()
    redis_mock.incr = Mock(return_value=42)
    redis_mock.ping = Mock(return_value=True)
    return redis_mock

@pytest.fixture
def mock_db_session():
    """Create a mock database session"""
    with patch('models.db.session') as mock_session:
        mock_session.add = Mock()
        mock_session.commit = Mock()
        yield mock_session

def test_clock_in_model():
    """Test ClockIn model can be instantiated"""
    from models.clock_in import ClockIn
    
    clock_in = ClockIn()
    assert clock_in is not None
    
    # Test to_dict method
    with patch.object(clock_in, 'clock_in_time') as mock_time:
        with patch.object(clock_in, 'created_at') as mock_created:
            mock_time.strftime = Mock(return_value='2026-01-13 09:30:00')
            mock_created.strftime = Mock(return_value='2026-01-13 09:30:00')
            clock_in.id = 1
            
            result = clock_in.to_dict()
            assert result['id'] == 1
            assert 'clock_in_time' in result
            assert 'created_at' in result

def test_clock_in_repository():
    """Test ClockInRepository methods"""
    from repositories.clock_in_repository import ClockInRepository
    
    repo = ClockInRepository()
    assert repo is not None
    assert hasattr(repo, 'find_recent')
    assert hasattr(repo, 'find_paginated')
    assert hasattr(repo, 'find_by_date_range')
    assert hasattr(repo, 'count_total')

def test_clock_in_service_without_redis(mock_db_session):
    """Test ClockInService create_clock_in without Redis"""
    from services.clock_in_service import ClockInService
    from models.clock_in import ClockIn
    
    # Mock repository
    mock_repo = Mock()
    mock_clock_in = ClockIn()
    mock_clock_in.id = 1
    mock_repo.save = Mock(return_value=mock_clock_in)
    mock_repo.count_total = Mock(return_value=5)
    
    # Create service without Redis
    service = ClockInService(repository=mock_repo, redis_client=None)
    
    # Test create_clock_in
    saved_record, count = service.create_clock_in()
    
    assert saved_record is not None
    assert count == 5
    mock_repo.save.assert_called_once()
    mock_repo.count_total.assert_called_once()

def test_clock_in_service_with_redis(mock_redis, mock_db_session):
    """Test ClockInService create_clock_in with Redis"""
    from services.clock_in_service import ClockInService
    from models.clock_in import ClockIn
    
    # Mock repository
    mock_repo = Mock()
    mock_clock_in = ClockIn()
    mock_clock_in.id = 1
    mock_repo.save = Mock(return_value=mock_clock_in)
    
    # Create service with Redis
    service = ClockInService(repository=mock_repo, redis_client=mock_redis)
    
    # Test create_clock_in
    saved_record, count = service.create_clock_in()
    
    assert saved_record is not None
    assert count == 42
    mock_repo.save.assert_called_once()
    mock_redis.incr.assert_called_once_with('daily_clock_in_count')

def test_clock_in_service_get_history():
    """Test ClockInService get_clock_in_history"""
    from services.clock_in_service import ClockInService
    from models.clock_in import ClockIn
    
    # Mock pagination
    mock_pagination = Mock()
    mock_pagination.total = 10
    mock_pagination.pages = 1
    mock_pagination.items = []
    
    # Mock repository
    mock_repo = Mock()
    mock_repo.find_paginated = Mock(return_value=mock_pagination)
    
    service = ClockInService(repository=mock_repo)
    
    # Test get_clock_in_history
    result = service.get_clock_in_history(page=1, per_page=20)
    
    assert result['total'] == 10
    assert result['page'] == 1
    assert result['per_page'] == 20
    assert result['total_pages'] == 1
    assert result['records'] == []
    mock_repo.find_paginated.assert_called_once_with(1, 20)

def test_clock_in_service_get_history_max_per_page():
    """Test ClockInService enforces max per_page limit"""
    from services.clock_in_service import ClockInService
    
    # Mock repository
    mock_repo = Mock()
    mock_pagination = Mock()
    mock_pagination.total = 200
    mock_pagination.pages = 2
    mock_pagination.items = []
    mock_repo.find_paginated = Mock(return_value=mock_pagination)
    
    service = ClockInService(repository=mock_repo)
    
    # Test with per_page > 100
    result = service.get_clock_in_history(page=1, per_page=200)
    
    # Should be capped at 100
    mock_repo.find_paginated.assert_called_once_with(1, 100)

def test_clock_in_schema():
    """Test ClockInResponseSchema"""
    from schemas.clock_in_schema import ClockInResponseSchema
    
    schema = ClockInResponseSchema()
    assert schema is not None
    
    # Test serialization
    data = {
        'id': 1,
        'clock_in_time': '2026-01-13 09:30:00',
        'created_at': '2026-01-13 09:30:00'
    }
    
    result = schema.dump(data)
    assert result['id'] == 1
    assert result['clock_in_time'] == '2026-01-13 09:30:00'
    assert result['created_at'] == '2026-01-13 09:30:00'

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
