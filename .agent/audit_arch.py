import os
import ast
import sys
from pathlib import Path
from typing import List, Tuple

# Definición de reglas de arquitectura (Quién NO puede importar a Quién)
# Formato: 'capa_origen': ['capa_prohibida1', 'capa_prohibida2']
FORBIDDEN_IMPORTS = {
    'app/domain': ['app.infra', 'app.services', 'app.api', 'pymongo', 'fastapi'],
    # 'app/api': ['app.infra'],  <-- PERMITIDO: Pragmático. Controladores pueden inyectar repositorios.
    # 'app/services': [], 
}

def get_imports(file_path: str) -> List[str]:
    """Extrae todos los imports de un archivo Python"""
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            tree = ast.parse(f.read(), filename=file_path)
        except SyntaxError:
            return []

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                imports.append(n.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports

def check_architecture(root_dir: str) -> List[str]:
    violations = []
    
    for root, _, files in os.walk(root_dir):
        for file in files:
            if not file.endswith('.py'):
                continue
                
            file_path = os.path.join(root, file)
            # Normalizar path para comparar con reglas
            rel_path = os.path.relpath(file_path, os.getcwd()).replace('\\', '/')
            
            # Determinar en qué capa estamos
            current_layer = None
            for layer in FORBIDDEN_IMPORTS.keys():
                if rel_path.startswith(layer):
                    current_layer = layer
                    break
            
            if not current_layer:
                continue
                
            # Chequear imports del archivo
            file_imports = get_imports(file_path)
            forbidden_list = FORBIDDEN_IMPORTS[current_layer]
            
            for imp in file_imports:
                for forbidden in forbidden_list:
                    if imp.startswith(forbidden):
                        violations.append(
                            f"❌ VIOLACIÓN: '{rel_path}' (Capa: {current_layer}) "
                            f"importa '{imp}' (Prohibido: {forbidden})"
                        )
                        
    return violations

if __name__ == "__main__":
    print("🔍 Iniciando Auditoría de Arquitectura SonqoBase...")
    print("------------------------------------------------")
    
    violations = check_architecture("app")
    
    if violations:
        print(f"😱 Se encontraron {len(violations)} violaciones de arquitectura:")
        for v in violations:
            print(v)
        sys.exit(1)
    else:
        print("✅ Arquitectura Limpia. ¡Buen trabajo!")
        sys.exit(0)
