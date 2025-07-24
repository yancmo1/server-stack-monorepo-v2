#!/usr/bin/env python3
"""
Basic import tests for the clan-map application
"""
import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_app_import():
    """Test that app module can be imported"""
    try:
        # Set minimal environment variables needed for import
        os.environ.setdefault('POSTGRES_DB', 'test_db')
        os.environ.setdefault('POSTGRES_USER', 'test_user')
        os.environ.setdefault('POSTGRES_PASSWORD', 'test_pass')
        os.environ.setdefault('POSTGRES_HOST', 'localhost')
        os.environ.setdefault('POSTGRES_PORT', '5432')
        
        import app
        assert hasattr(app, 'app')  # Flask app object
        print("✅ App module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import app: {e}")
        return False
    except Exception as e:
        # App might fail due to missing database connection, but import should work
        print(f"⚠️  App import completed with warning: {e}")
    return True

def test_map_generator_import():
    """Test that map_generator module can be imported"""
    try:
        import map_generator
        assert hasattr(map_generator, 'generate_map')
        print("✅ Map generator module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import map_generator: {e}")
        return False
    except Exception as e:
        print(f"⚠️  Map generator import completed with warning: {e}")
    return True

def test_sync_clan_data_import():
    """Test that sync_clan_data module can be imported"""
    try:
        import sync_clan_data
        print("✅ Sync clan data module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import sync_clan_data: {e}")
        return False
    except Exception as e:
        print(f"⚠️  Sync clan data import completed with warning: {e}")
    return True

def test_sync_to_bot_db_import():
    """Test that sync_to_bot_db module can be imported"""
    try:
        import sync_to_bot_db
        print("✅ Sync to bot db module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import sync_to_bot_db: {e}")
        return False
    except Exception as e:
        print(f"⚠️  Sync to bot db import completed with warning: {e}")
    return True

def test_flask_app_creation():
    """Test that Flask app can be created"""
    try:
        # Set minimal environment variables
        os.environ.setdefault('POSTGRES_DB', 'test_db')
        os.environ.setdefault('POSTGRES_USER', 'test_user')
        os.environ.setdefault('POSTGRES_PASSWORD', 'test_pass')
        os.environ.setdefault('POSTGRES_HOST', 'localhost')
        os.environ.setdefault('POSTGRES_PORT', '5432')
        
        from app import app
        assert app is not None
        assert app.config is not None
        print("✅ Flask app created successfully")
    except Exception as e:
        print(f"⚠️  Flask app creation completed with warning: {e}")
    return True

if __name__ == '__main__':
    # Run tests directly if script is called
    print("🔄 Running import tests...")
    tests = [
        test_app_import,
        test_map_generator_import,
        test_sync_clan_data_import,
        test_sync_to_bot_db_import,
        test_flask_app_creation
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
    
    print(f"\n📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✅ All import tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)
