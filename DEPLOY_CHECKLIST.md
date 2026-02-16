# ✅ Checklist de Despliegue

Sigue estos pasos **en orden** para evitar errores:

## 📦 Paso 1: Preparar archivos localmente

### 1.1 Verificar estructura
Ejecuta el script de verificación:
```bash
python test_imports.py
```

Deberías ver:
```
🎉 ¡Todo está correcto!
```

### 1.2 Verificar que existen estos archivos:
- [ ] `app.py`
- [ ] `requirements.txt`
- [ ] `.gitignore`
- [ ] `services/__init__.py` ← **MUY IMPORTANTE**
- [ ] `services/firebase_service.py`
- [ ] `services/calculation_service.py`
- [ ] `services/pdf_service.py`
- [ ] `models/__init__.py` ← **MUY IMPORTANTE**
- [ ] `models/project_model.py`
- [ ] `pages/1_Proyectos.py`
- [ ] `pages/2_Referencias.py`

### 1.3 Archivos que NO deben subirse:
- [ ] `firebase-credentials.json` (debe estar en .gitignore)
- [ ] `__pycache__/`
- [ ] `.streamlit/secrets.toml`

## 🔥 Paso 2: Configurar Firebase

1. Crear proyecto en [Firebase Console](https://console.firebase.google.com/)
2. Activar **Firestore Database** (modo producción)
3. Descargar credenciales (Settings > Service Accounts > Generate new private key)
4. Guardar como `firebase-credentials.json` (NO subir a Git)

## 📤 Paso 3: Subir a GitHub

```bash
# Inicializar repo (si no existe)
git init

# Agregar archivos
git add .

# Verificar que los __init__.py se agregaron
git status

# Si no aparecen, agregarlos explícitamente:
git add services/__init__.py
git add models/__init__.py
git add .streamlit/config.toml

# Commit
git commit -m "Initial commit - Carpintería app"

# Conectar con GitHub
git remote add origin https://github.com/TU_USUARIO/TU_REPO.git

# Push
git branch -M main
git push -u origin main
```

## ☁️ Paso 4: Desplegar en Streamlit Cloud

### 4.1 Configurar app
1. Ir a [share.streamlit.io](https://share.streamlit.io)
2. "New app"
3. Seleccionar tu repositorio
4. Branch: `main`
5. Main file path: `app.py`

### 4.2 Configurar Secrets
En "Advanced settings" > "Secrets", pegar:

```toml
[firebase]
type = "service_account"
project_id = "tu-project-id"
private_key_id = "..."
private_key = """-----BEGIN PRIVATE KEY-----
TU_CLAVE_COMPLETA_AQUI
-----END PRIVATE KEY-----"""
client_email = "firebase-adminsdk-xxxxx@tu-project.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
universe_domain = "googleapis.com"
```

**Copiar valores de tu `firebase-credentials.json`**

### 4.3 Deploy
Hacer clic en "Deploy" y esperar 2-3 minutos.

## 🐛 Si hay errores

### Error: "No module named 'services'"

**Causa**: Los archivos `__init__.py` no se subieron.

**Solución**:
```bash
git add services/__init__.py
git add models/__init__.py
git commit -m "Add __init__ files"
git push
```

Luego en Streamlit Cloud: "Reboot app"

### Error: "Could not find firebase credentials"

**Causa**: Secrets mal configurados.

**Solución**:
1. Verificar que el formato sea TOML (no JSON)
2. Verificar que la `private_key` tenga las comillas triples `"""`
3. Verificar que NO haya espacios extra

### Error: "Connection to Firebase failed"

**Causa**: Firestore no activado o credenciales incorrectas.

**Solución**:
1. Ir a Firebase Console
2. Verificar que Firestore esté activado
3. Re-generar credenciales si es necesario

### La app carga pero da error al abrir

**Causa**: Error en tiempo de ejecución (no de imports).

**Solución**:
1. Ver logs en Streamlit Cloud
2. Verificar que Firestore esté activado
3. Probar en "Manage app" > "Logs"

## ✅ Verificación Final

Una vez desplegado:
1. [ ] La app carga sin errores
2. [ ] Puedes navegar a "Referencias"
3. [ ] Puedes crear un material de prueba
4. [ ] Puedes crear un proyecto de prueba
5. [ ] Puedes generar un PDF

Si todo funciona: **¡Listo! 🎉**

## 📞 Necesitas ayuda?

Revisa:
1. `SOLUCION_IMPORTS.md` - Solución a errores de imports
2. `INICIO_RAPIDO.md` - Guía completa paso a paso
3. `README.md` - Documentación general

O contacta con la información del error completo.
