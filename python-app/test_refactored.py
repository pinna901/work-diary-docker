"""
Integration tests for the refactored application
"""
import pytest
import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

def test_can_import_app():
    """Test that we can import the main app module"""
    from app import create_app
    assert create_app is not None

def test_can_import_config():
    """Test that we can import config"""
    from config import config
    assert config is not None
    assert 'development' in config
    assert 'production' in config

def test_can_import_models():
    """Test that we can import models"""
    from models import db
    from models.diary import Diary
    assert db is not None
    assert Diary is not None

def test_can_import_repositories():
    """Test that we can import repositories"""
    from repositories.base_repository import BaseRepository
    from repositories.diary_repository import DiaryRepository
    assert BaseRepository is not None
    assert DiaryRepository is not None

def test_can_import_services():
    """Test that we can import services"""
    from services.cache_service import CacheService
    from services.quote_service import QuoteService
    from services.ai_service import AIService
    from services.diary_service import DiaryService
    assert CacheService is not None
    assert QuoteService is not None
    assert AIService is not None
    assert DiaryService is not None

def test_can_import_routes():
    """Test that we can import routes"""
    from routes.health import health_bp
    from routes.api.v1 import api_v1_bp
    assert health_bp is not None
    assert api_v1_bp is not None

def test_can_import_schemas():
    """Test that we can import schemas"""
    from schemas.diary_schema import DiaryCreateSchema, DiaryResponseSchema
    assert DiaryCreateSchema is not None
    assert DiaryResponseSchema is not None

def test_can_import_utils():
    """Test that we can import utils"""
    from utils import add
    from utils.decorators import validate_json
    from utils.exceptions import AppException, ValidationError
    assert add is not None
    assert validate_json is not None
    assert AppException is not None
    assert ValidationError is not None

def test_utils_add_function():
    """Test the utils add function still works"""
    from utils import add
    assert add(1, 1) == 2
    assert add(-1, 1) == 0

def test_cache_service_initialization():
    """Test that cache service can initialize"""
    from services.cache_service import CacheService
    cache = CacheService()
    # Should initialize even if Redis is not available
    assert cache is not None
    assert hasattr(cache, 'enabled')
    assert hasattr(cache, 'get_stats')
    
    # Test stats
    stats = cache.get_stats()
    assert 'enabled' in stats
    assert 'hits' in stats
    assert 'misses' in stats

def test_ai_service_initialization():
    """Test that AI service can initialize"""
    from services.ai_service import AIService
    ai = AIService()
    assert ai is not None
    assert hasattr(ai, 'is_available')

def test_quote_service_initialization():
    """Test that quote service can initialize"""
    from services.quote_service import QuoteService
    quote = QuoteService()
    assert quote is not None
    assert hasattr(quote, 'get_daily_quote')

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
