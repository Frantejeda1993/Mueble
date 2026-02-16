# 🔧 Solución a Error de Imports

Si ves este error al desplegar:
```
ModuleNotFoundError: No module named 'services'
```

## Solución 1: Verificar estructura de archivos

Asegúrate de que la estructura sea EXACTAMENTE así:

```
tu-repositorio/
├── app.py
├── requirements.txt
├── pages/
│   ├── 1_Proyectos.py
│   └── 2_Referencias.py
├── services/
│   ├── __init__.py          ← IMPORTANTE
│   ├── firebase_service.py
│   ├── calculation_service.py
│   └── pdf_service.py
└── models/
    ├── __init__.py          ← IMPORTANTE
    └── project_model.py
```

**CRÍTICO**: Los archivos `__init__.py` DEBEN existir (aunque estén vacíos).

## Solución 2: Verificar que subiste todos los archivos

En GitHub, verifica que todas las carpetas `services/` y `models/` estén presentes con sus archivos.

A veces Git no sube carpetas vacías o archivos `__init__.py`.

### Comando para verificar en terminal:
```bash
git add services/__init__.py
git add models/__init__.py
git commit -m "Add __init__.py files"
git push
```

## Solución 3: Esperar a que Streamlit termine de instalar

A veces el error aparece durante la instalación. Espera 2-3 minutos y refresca la página.

## Solución 4: Verificar requirements.txt

Asegúrate de que `requirements.txt` contenga:
```
streamlit>=1.28.0
firebase-admin>=6.2.0
google-cloud-firestore>=2.13.0
reportlab>=4.0.0
matplotlib>=3.7.0
Pillow>=10.0.0
```

## Solución 5: Limpiar caché de Streamlit Cloud

1. Ve a tu app en Streamlit Cloud
2. Click en "⋮" (menú)
3. "Reboot app"

## Solución 6: Si nada funciona - Usar imports absolutos

Crea un archivo `.streamlit/config.toml` en la raíz:

```toml
[server]
enableCORS = false
enableXsrfProtection = false
```

Y modifica los imports en `app.py`:

```python
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.firebase_service import FirebaseService
```

## Verificación Rápida

Crea un archivo `test_imports.py` en la raíz:

```python
try:
    from services.firebase_service import FirebaseService
    print("✅ Import exitoso")
except Exception as e:
    print(f"❌ Error: {e}")
```

Ejecuta localmente:
```bash
python test_imports.py
```

Si funciona localmente pero falla en Streamlit Cloud, el problema es la configuración del deploy.

## ¿Sigue sin funcionar?

Mándame:
1. Screenshot del error completo
2. Estructura de carpetas de tu repo GitHub
3. Contenido de tu requirements.txt

Y te ayudo a resolverlo específicamente.
