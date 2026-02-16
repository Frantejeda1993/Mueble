# 🚀 Guía de Inicio Rápido

## Paso 1: Configurar Firebase

### 1.1 Crear Proyecto Firebase
1. Ve a https://console.firebase.google.com/
2. Haz clic en "Agregar proyecto"
3. Nombra tu proyecto (ej: "carpinteria-presupuestos")
4. Desactiva Google Analytics (no es necesario)
5. Haz clic en "Crear proyecto"

### 1.2 Activar Firestore
1. En el menú lateral, selecciona "Firestore Database"
2. Haz clic en "Crear base de datos"
3. Selecciona "Modo de producción"
4. Elige la ubicación más cercana a ti
5. Haz clic en "Habilitar"

### 1.3 Obtener Credenciales
1. Ve a "Configuración del proyecto" (ícono de engranaje)
2. Pestaña "Cuentas de servicio"
3. Haz clic en "Generar nueva clave privada"
4. Se descargará un archivo JSON
5. Renombra el archivo a `firebase-credentials.json`

## Paso 2: Instalación Local (Opcional)

```bash
# Clonar o descargar el proyecto
cd carpinteria-presupuestos

# Instalar dependencias
pip install -r requirements.txt

# Copiar credenciales
# Coloca firebase-credentials.json en la raíz del proyecto

# Ejecutar
streamlit run app.py
```

## Paso 3: Despliegue en Streamlit Cloud

### 3.1 Subir a GitHub
1. Crea un repositorio en GitHub
2. Sube todos los archivos EXCEPTO:
   - `firebase-credentials.json`
   - Carpeta `.streamlit/` si existe

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/tu-usuario/tu-repo.git
git push -u origin main
```

### 3.2 Desplegar en Streamlit Cloud
1. Ve a https://streamlit.io/cloud
2. Inicia sesión con GitHub
3. Haz clic en "New app"
4. Selecciona tu repositorio
5. Branch: `main`
6. Main file: `app.py`
7. Haz clic en "Advanced settings"

### 3.3 Configurar Secrets
En la sección "Secrets", pega el siguiente contenido (reemplaza con tus valores):

```toml
[firebase]
type = "service_account"
project_id = "tu-project-id"
private_key_id = "abc123..."
private_key = """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...
TU CLAVE COMPLETA AQUÍ (incluye los saltos de línea)
-----END PRIVATE KEY-----"""
client_email = "firebase-adminsdk-xxxxx@tu-project.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
universe_domain = "googleapis.com"
```

**IMPORTANTE**: 
- Copia los valores de tu archivo `firebase-credentials.json`
- La `private_key` debe incluir las comillas triples `"""` y los saltos de línea

### 3.4 Deploy
Haz clic en "Deploy" y espera unos minutos.

## Paso 4: Primer Uso

### 4.1 Configurar Referencias
1. Ve a la página "Referencias"
2. Agrega tu primer material:
   - Tipo: Melamina
   - Color: Blanco
   - Espesor: 18mm
   - Desperdicio: 0.10 (10%)
   - Precio tabla: 45€
   - Dimensiones tabla: 2440 × 1220 mm

3. Agrega herrajes comunes:
   - Bisagra: 2.50€
   - Tirador: 3.00€
   - Guía cajón: 8.50€

4. Configura servicio de corte:
   - Precio/m²: 5.00€
   - Desperdicio: 0.10 (10%)

5. Sube tu logo (PNG, 500x500px recomendado)

### 4.2 Crear Primer Proyecto
1. Ve a "Proyectos"
2. Haz clic en "Nuevo Proyecto"
3. Completa información básica:
   - Nombre: "Mueble Cocina"
   - Cliente: "Juan Pérez"
   - Fecha: hoy
   - Estado: Activo

4. Agrega un módulo:
   - Alto: 2000mm
   - Ancho: 1000mm
   - Profundidad: 400mm
   - Material: Melamina Blanco 18mm
   - Con fondo: Sí
   - Con puertas: 2
   - Estantes: 2

5. Agrega herrajes:
   - Bisagras × 4
   - Tiradores × 2

6. Define costos:
   - Mano de obra: 200€
   - Complejidad: 50€

7. Guarda el proyecto

### 4.3 Generar PDF
1. Ve a la pestaña "PDF"
2. Haz clic en "Descargar PDF"
3. Revisa el presupuesto generado

## 🎯 ¡Listo!

Tu sistema está funcionando. Ahora puedes:
- ✅ Crear múltiples proyectos
- ✅ Agregar más materiales y herrajes
- ✅ Ver cálculos automáticos
- ✅ Generar PDFs profesionales

## 📞 ¿Problemas?

### Error: "No se puede conectar con Firebase"
- Verifica que las credenciales sean correctas
- Asegúrate de haber activado Firestore

### Error: "Module not found"
- En Streamlit Cloud: espera a que termine la instalación
- En local: ejecuta `pip install -r requirements.txt`

### El PDF no incluye el logo
- Verifica que hayas subido el logo en "Referencias" > pestaña "Logo"
- Comprueba que el archivo sea PNG o JPG y menor a 1MB
- El logo se guarda en Firestore como base64

### Los cálculos parecen incorrectos
- Verifica que los materiales tengan dimensiones de tabla configuradas
- Los factores de desperdicio deben ser decimales (0.10 = 10%, no 10)
- Asegúrate de guardar los cambios antes de calcular

## 💡 Consejos

1. **Materiales**: Crea materiales para cada combinación tipo-color-espesor
2. **Herrajes**: Agrega los herrajes más comunes con precio para agilizar
3. **Backup**: Exporta regularmente desde Firebase Console
4. **Precios**: Actualiza los precios periódicamente
5. **Logo**: Usa un logo con fondo transparente para mejor resultado en PDF

---

**¡Disfruta tu sistema de presupuestos!** 🪵✨
