"""
Script para generar una clave de encriptación Fernet.
Ejecutar una vez y agregar el resultado a .env como ENCRYPTION_KEY
"""
from app.utils.encryption import generate_encryption_key

if __name__ == "__main__":
    key = generate_encryption_key()
    print("\n" + "="*60)
    print("🔐 ENCRYPTION KEY GENERATED")
    print("="*60)
    print("\nAdd this line to your .env file:")
    print(f"\nENCRYPTION_KEY={key}")
    print("\n" + "="*60)
    print("⚠️  IMPORTANT: Keep this key secret and never commit it to git!")
    print("="*60 + "\n")
