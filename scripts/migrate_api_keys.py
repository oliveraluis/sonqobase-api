"""
Script de migración para encriptar API keys existentes.
Ejecutar una sola vez después de agregar ENCRYPTION_KEY al .env
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.infra.mongo_client import get_mongo_client
from app.config import settings
from app.utils.encryption import encrypt_api_key
import hashlib


def _hash_api_key(api_key: str) -> str:
    """Hash API key usando SHA-256"""
    return hashlib.sha256(api_key.encode()).hexdigest()


def migrate_project_api_key(project_id: str, api_key: str):
    """
    Migrar un proyecto específico agregando la API key encriptada.
    
    Args:
        project_id: ID del proyecto
        api_key: La API key en texto plano
    """
    client = get_mongo_client()
    meta_db = client[settings.mongo_meta_db]
    
    # Verificar que el proyecto existe
    project = meta_db.projects.find_one({"project_id": project_id})
    
    if not project:
        print(f"❌ Error: Project {project_id} not found")
        return False
    
    # Verificar que la API key es correcta (comparar hash)
    api_key_hash = _hash_api_key(api_key)
    
    if project.get("api_key_hash") != api_key_hash:
        print(f"❌ Error: API key does not match for project {project_id}")
        return False
    
    # Verificar si ya tiene api_key_encrypted
    if "api_key_encrypted" in project:
        print(f"⚠️  Warning: Project {project_id} already has encrypted API key")
        return True
    
    # Encriptar y guardar
    try:
        encrypted_key = encrypt_api_key(api_key)
        
        result = meta_db.projects.update_one(
            {"project_id": project_id},
            {"$set": {"api_key_encrypted": encrypted_key}}
        )
        
        if result.modified_count > 0:
            print(f"✅ Successfully migrated project {project_id} ({project.get('name', 'Unknown')})")
            return True
        else:
            print(f"❌ Failed to update project {project_id}")
            return False
            
    except Exception as e:
        print(f"❌ Error encrypting API key for project {project_id}: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔐 PROJECT API KEY MIGRATION")
    print("="*60 + "\n")
    
    # Verificar que ENCRYPTION_KEY está configurada
    if not settings.encryption_key:
        print("❌ Error: ENCRYPTION_KEY not set in .env file")
        print("Run: python scripts/generate_encryption_key.py")
        sys.exit(1)
    
    print(f"✓ ENCRYPTION_KEY configured")
    print(f"✓ MongoDB URI: {settings.mongo_uri[:30]}..." if settings.mongo_uri else "❌ MongoDB URI not set")
    print()
    
    # Proyecto a migrar
    PROJECT_ID = "proj_c5d22237"
    API_KEY = "sonqo_proj_1f9f26acd7cbc9c27b18e6d5b8587d0a"
    
    print(f"Migrating project: {PROJECT_ID}")
    print(f"API Key: {API_KEY[:20]}...")
    print()
    
    try:
        success = migrate_project_api_key(PROJECT_ID, API_KEY)
        
        print("\n" + "="*60)
        if success:
            print("✅ MIGRATION COMPLETED SUCCESSFULLY")
            print("\nYou can now view the API key in the dashboard!")
        else:
            print("❌ MIGRATION FAILED")
        print("="*60 + "\n")
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        print("\nPossible causes:")
        print("  - MongoDB is not running")
        print("  - MONGO_URI in .env is incorrect")
        print("  - Network connection issues")
        print("\n" + "="*60 + "\n")
        sys.exit(1)
