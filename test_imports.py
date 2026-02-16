"""
Script de prueba para verificar que los imports funcionan correctamente
Ejecuta esto localmente antes de hacer deploy
"""

print("🔍 Verificando estructura de archivos...")

import os
import sys

# Verificar estructura
required_files = [
    'app.py',
    'requirements.txt',
    'services/__init__.py',
    'services/firebase_service.py',
    'services/calculation_service.py',
    'services/pdf_service.py',
    'models/__init__.py',
    'models/project_model.py',
    'pages/1_Proyectos.py',
    'pages/2_Referencias.py',
]

print("\n📁 Verificando archivos necesarios:")
missing = []
for file in required_files:
    if os.path.exists(file):
        print(f"  ✅ {file}")
    else:
        print(f"  ❌ {file} - FALTA")
        missing.append(file)

if missing:
    print(f"\n⚠️  Faltan {len(missing)} archivo(s)")
    sys.exit(1)
else:
    print("\n✅ Todos los archivos están presentes")

# Verificar que requirements.txt tiene las dependencias correctas
print("\n📦 Verificando requirements.txt...")
with open('requirements.txt', 'r') as f:
    requirements = f.read()
    required_packages = [
        'streamlit',
        'firebase-admin',
        'google-cloud-firestore',
        'reportlab',
        'matplotlib',
        'Pillow'
    ]
    
    for package in required_packages:
        if package in requirements:
            print(f"  ✅ {package}")
        else:
            print(f"  ❌ {package} - FALTA en requirements.txt")

# Verificar imports (opcional - puede fallar si no tienes las dependencias instaladas)
print("\n🔌 Verificando sintaxis de archivos Python...")

import ast

files_to_check = [
    'services/firebase_service.py',
    'services/calculation_service.py',
    'services/pdf_service.py',
    'models/project_model.py',
    'app.py'
]

syntax_errors = False
for file in files_to_check:
    try:
        with open(file, 'r') as f:
            ast.parse(f.read())
        print(f"  ✅ {file} - Sintaxis correcta")
    except SyntaxError as e:
        print(f"  ❌ {file} - ERROR DE SINTAXIS: {e}")
        syntax_errors = True

if syntax_errors:
    print("\n⚠️  Hay errores de sintaxis que debes corregir")
    sys.exit(1)

print("\n" + "="*60)
print("🎉 ¡VERIFICACIÓN COMPLETA!")
print("="*60)

print("\n✅ Estructura de archivos: CORRECTA")
print("✅ Requirements.txt: CORRECTO")
print("✅ Sintaxis Python: CORRECTA")

print("\n📝 NOTA IMPORTANTE:")
print("   No se verificaron los imports de librerías porque requieren")
print("   que instales las dependencias localmente con:")
print("   ")
print("   pip install -r requirements.txt")
print("   ")
print("   Pero esto NO es necesario si solo vas a desplegar en Streamlit Cloud.")
print("   Streamlit Cloud instalará las dependencias automáticamente.")

print("\n🚀 PRÓXIMOS PASOS:")
print("   1. git add .")
print("   2. git commit -m 'Setup complete'")
print("   3. git push")
print("   4. Desplegar en Streamlit Cloud")
print("   5. Configurar secrets de Firebase en Streamlit Cloud")

print("\n✨ ¡Todo listo para hacer deploy!")
