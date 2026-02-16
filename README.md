# 🪵 Sistema de Presupuestos de Carpintería

Aplicación web desarrollada en Streamlit para gestionar presupuestos de proyectos de carpintería.

## 🚀 Características

- ✅ Gestión completa de proyectos de carpintería
- 📦 Módulos personalizables con laterales, horizontales, fondos, puertas, estantes y divisiones
- 📏 Estantes y maderas independientes
- 🔩 Gestión de herrajes
- 💰 Cálculos automáticos de materiales, corte y costos
- 📊 Visualización gráfica de módulos
- 📄 Generación de PDFs profesionales con logo
- 🔥 Base de datos en Firebase Firestore

## 📋 Requisitos Previos

1. **Cuenta de Firebase**
   - Crear un proyecto en [Firebase Console](https://console.firebase.google.com/)
   - Activar Firestore Database
   - Descargar las credenciales del proyecto (archivo JSON)

2. **Python 3.8+**

## 🛠️ Instalación Local

1. Clonar o descargar el proyecto

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Configurar Firebase:
   - Descargar el archivo de credenciales de Firebase
   - Guardarlo como `firebase-credentials.json` en la raíz del proyecto

4. Ejecutar la aplicación:
```bash
streamlit run app.py
```

## ☁️ Despliegue en Streamlit Cloud

1. **Subir el código a GitHub**
   - Crear un repositorio en GitHub
   - Subir todos los archivos EXCEPTO `firebase-credentials.json`

2. **Configurar Secrets en Streamlit Cloud**
   - Ir a [Streamlit Cloud](https://streamlit.io/cloud)
   - Conectar tu repositorio de GitHub
   - En "Advanced settings" > "Secrets", agregar:

```toml
[firebase]
type = "service_account"
project_id = "tu-project-id"
private_key_id = "tu-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nTU_PRIVATE_KEY\n-----END PRIVATE KEY-----\n"
client_email = "tu-client-email@tu-project.iam.gserviceaccount.com"
client_id = "tu-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "tu-cert-url"
storage_bucket = "tu-project.appspot.com"
```

   **IMPORTANTE**: Los valores deben copiarse desde tu archivo `firebase-credentials.json`

3. **Deploy**
   - Hacer clic en "Deploy"
   - La aplicación estará disponible en pocos minutos

## 📁 Estructura del Proyecto

```
├── app.py                          # Página principal
├── pages/
│   ├── 1_Proyectos.py             # Gestión de proyectos
│   └── 2_Referencias.py           # Configuración de materiales y herrajes
├── services/
│   ├── firebase_service.py        # Conexión con Firebase
│   ├── calculation_service.py     # Lógica de cálculos
│   └── pdf_service.py             # Generación de PDFs
├── models/
│   └── project_model.py           # Modelo de datos
└── requirements.txt                # Dependencias
```

## 🔥 Estructura de Firebase

### Colecciones en Firestore:

**projects**
```json
{
  "name": "Nombre del proyecto",
  "client": "Nombre del cliente",
  "date": "Timestamp",
  "status": "Activo" | "Cerrado",
  "modules": [],
  "shelves": [],
  "woods": [],
  "hardwares": [],
  "labor_cost_project": 0,
  "extra_complexity": 0,
  "final_price": 0,
  "totals": {}
}
```

**materials**
```json
{
  "type": "Melamina",
  "color": "Blanco",
  "thickness_mm": 18,
  "waste_factor": 0.10,
  "board_price": 45.50,
  "board_height_mm": 2440,
  "board_width_mm": 1220
}
```

**hardware**
```json
{
  "type": "Bisagra",
  "price_unit": 2.50,
  "link": "https://...",
  "image_url": "https://..."
}
```

**cutting_service** (documento único con ID "config")
```json
{
  "price_per_m2": 5.00,
  "waste_factor": 0.10
}
```

**config** (colección para configuración general)
- Documento `logo`: Almacena el logo en formato base64
```json
{
  "logo_base64": "iVBORw0KGgoAAAANS...",
  "updated_at": "Timestamp"
}
```

## 💡 Uso de la Aplicación

### 1. Configurar Referencias
   - Ir a "Referencias"
   - Agregar materiales (tipos de madera, precios, dimensiones de tablas)
   - Agregar herrajes comunes
   - Configurar servicio de corte
   - Subir logo

### 2. Crear Proyecto
   - Ir a "Proyectos"
   - Crear nuevo proyecto
   - Agregar módulos, estantes, maderas
   - Seleccionar herrajes
   - Definir costos de mano de obra

### 3. Generar Presupuesto
   - Ver cálculos automáticos
   - Ajustar precio final si es necesario
   - Visualizar diseño gráfico
   - Descargar PDF

## 🧮 Lógica de Cálculo

### Superficies de Módulos:
- 2 laterales: alto × profundo
- 2 horizontales: ancho × profundo
- Fondo (opcional): ancho × alto
- Puertas: ancho × alto × cantidad
- Estantes: ancho × profundo × cantidad
- Divisiones: alto × profundo × cantidad

**NOTA**: NO se descuentan espesores

### Cálculo de Materiales:
1. Sumar m² por tipo de material
2. Aplicar factor de desperdicio
3. Calcular tablas necesarias
4. Multiplicar por precio de tabla

### Costo de Corte:
```
costo_corte = m²_con_desperdicio × precio_m² × (1 + factor_desperdicio_corte)
```

### Mano de Obra en PDF:
```
mano_obra_pdf = labor_cost_project + extra_complexity + (final_price - total_calculated)
```

## 🐛 Solución de Problemas

**Error de conexión con Firebase:**
- Verificar que las credenciales sean correctas
- Asegurar que Firestore esté activado

**Error al generar PDF:**
- Verificar que el logo esté subido en Referencias
- Comprobar que todos los materiales tengan precios

**Cálculos incorrectos:**
- Verificar que los materiales tengan configuradas las dimensiones de tabla
- Revisar factores de desperdicio (deben ser decimales, ej: 0.10 para 10%)

## 📞 Soporte

Para problemas o mejoras, consultar la documentación de:
- [Streamlit](https://docs.streamlit.io/)
- [Firebase](https://firebase.google.com/docs)
- [ReportLab](https://www.reportlab.com/docs/)

## 📝 Licencia

Proyecto de uso personal.

---

**Desarrollado con ❤️ para facilitar la gestión de presupuestos de carpintería**
