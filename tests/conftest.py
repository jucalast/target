"""Pytest configuration and fixtures for integration tests.

This module provides test configuration and fixtures for the integration tests.
It sets up the test database and provides fixtures for testing.
"""
import os
import pytest
import sys
from pathlib import Path
from typing import Generator, Dict, Any

# Add backend directory to Python path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Set test environment variables
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5432/target_db"
os.environ["MONGO_URI"] = "mongodb://admin:admin@localhost:27017/target_db?authSource=admin"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-1234567890"
os.environ["JWT_ALGORITHM"] = "HS256"

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pymongo import MongoClient

# Create Base for testing
Base = declarative_base()

# Create test database engine
engine = create_engine("postgresql://postgres:postgres@localhost:5432/target_db")
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# MongoDB client
mongo_client = MongoClient("mongodb://admin:admin@localhost:27017/target_db?authSource=admin")

@pytest.fixture(scope="session")
def db_engine() -> Generator:
    """Create test database and tables."""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def test_db(db_engine) -> Generator[Dict[str, Any], None, None]:
    """Create database session for testing."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    # MongoDB database
    mongo_db = mongo_client.get_database("target_db")
    
    yield {
        'postgres': session,
        'mongo': mongo_db
    }
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def auth_headers() -> Dict[str, str]:
    """Generate JWT auth headers for testing."""
    return {"Authorization": "Bearer test-token"}

@pytest.fixture(scope="function")
def admin_auth_headers() -> Dict[str, str]:
    """Generate JWT auth headers with admin privileges for testing."""
    return {"Authorization": "Bearer admin-test-token"}
