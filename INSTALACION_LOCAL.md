# 💻 Instalación Local (Opcional)

Esta guía es OPCIONAL. Solo necesitas esto si quieres probar la app localmente antes de desplegarla.

**Si solo vas a desplegar en Streamlit Cloud, NO necesitas hacer esto.**

## ¿Por qué instalar localmente?

- ✅ Probar cambios antes de hacer deploy
- ✅ Desarrollar nuevas funcionalidades
- ✅ Debugging más fácil

## Requisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

## Pasos de Instalación

### 1. Crear entorno virtual (recomendado)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

Esto instalará:
- streamlit
- firebase-admin
- google-cloud-firestore
- reportlab
- matplotlib
- Pillow

**Nota**: La instalación puede tardar 2-5 minutos.

### 3. Configurar credenciales de Firebase

1. Descarga tu archivo de credenciales de Firebase
2. Guárdalo como `firebase-credentials.json` en la raíz del proyecto

### 4. Ejecutar la aplicación

```bash
streamlit run app.py
```

La app se abrirá en tu navegador en `http://localhost:8501`

## Solución de Problemas

### Error: "python: command not found"

**Solución**: Instala Python desde https://www.python.org/downloads/

### Error: "pip: command not found"

**Solución**: 
```bash
python -m ensurepip --upgrade
```

### Error al instalar dependencias

**Solución**: Actualiza pip
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Error: "No module named 'streamlit'"

**Solución**: Asegúrate de haber activado el entorno virtual y instalado las dependencias.

### La app da error de Firebase

**Causa**: No tienes el archivo `firebase-credentials.json`

**Solución**: 
1. Ve a Firebase Console
2. Descarga las credenciales
3. Guárdalas como `firebase-credentials.json` en la raíz

## Desarrollo

### Estructura para desarrollo

```
proyecto/
├── venv/                      ← Entorno virtual (no subir a Git)
├── firebase-credentials.json  ← Credenciales (no subir a Git)
├── app.py
├── requirements.txt
├── services/
├── models/
└── pages/
```

### Hacer cambios

1. Modifica los archivos
2. Streamlit recargará automáticamente
3. Si cambias dependencias, actualiza `requirements.txt`

### Guardar cambios en Git

```bash
git add .
git commit -m "Descripción de cambios"
git push
```

**IMPORTANTE**: El archivo `firebase-credentials.json` NO debe subirse a Git. Está en `.gitignore`.

## Desactivar entorno virtual

Cuando termines de trabajar:

```bash
deactivate
```

## ¿Necesitas ayuda?

Si tienes problemas con la instalación local:
1. Verifica que Python 3.8+ esté instalado: `python --version`
2. Verifica que pip funcione: `pip --version`
3. Intenta crear un nuevo entorno virtual

Recuerda: **La instalación local es OPCIONAL**. Puedes desarrollar y desplegar directamente en Streamlit Cloud sin necesidad de instalar nada localmente.
