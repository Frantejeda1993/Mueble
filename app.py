import streamlit as st
from services.firebase_service import FirebaseService

# Configuración de la página
st.set_page_config(
    page_title="Presupuestos Carpintería",
    page_icon="🪵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar Firebase
def init_firebase():
    """Inicializa la conexión con Firebase"""
    try:
        with st.spinner("Conectando con Firebase..."):
            return FirebaseService()
    except Exception as e:
        st.error("❌ No se pudo conectar con Firebase")
        st.error(f"Error: {str(e)}")
        st.info("""
        **Pasos para solucionar:**
        
        1. **Verifica que Firestore esté activado:**
           - Ve a Firebase Console
           - Selecciona tu proyecto
           - Ve a "Firestore Database"
           - Si no está activado, haz clic en "Crear base de datos"
        
        2. **Verifica las credenciales (Streamlit Cloud):**
           - Ve a tu app en Streamlit Cloud
           - Settings > Secrets
           - Verifica que tengas todos los campos del archivo secrets.example.toml
        
        3. **Verifica las credenciales (Local):**
           - Asegúrate de tener firebase-credentials.json en la raíz
        """)
        st.stop()

# Inicializar solo una vez
if 'firebase' not in st.session_state:
    st.session_state.firebase = init_firebase()

firebase = st.session_state.firebase

# Página principal
st.title("🪵 Sistema de Presupuestos de Carpintería")
st.markdown("""
Bienvenido al sistema de gestión de presupuestos.

Utiliza el menú lateral para navegar entre:
- **Proyectos**: Gestiona tus presupuestos
- **Referencias**: Configura materiales, herrajes y servicios
""")

# Estadísticas rápidas
st.subheader("📊 Resumen")
col1, col2, col3 = st.columns(3)

try:
    projects = firebase.get_all_projects()
    active_projects = [p for p in projects if p.get('status') == 'Activo']
    closed_projects = [p for p in projects if p.get('status') == 'Cerrado']
    
    with col1:
        st.metric("Proyectos Activos", len(active_projects))
    with col2:
        st.metric("Proyectos Cerrados", len(closed_projects))
    with col3:
        st.metric("Total Proyectos", len(projects))
except Exception as e:
    st.warning(f"No se pudieron cargar las estadísticas: {str(e)}")

st.markdown("---")
st.info("💡 Selecciona una página del menú lateral para comenzar")
