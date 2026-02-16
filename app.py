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
@st.cache_resource
def init_firebase():
    """Inicializa la conexión con Firebase"""
    try:
        return FirebaseService()
    except Exception as e:
        st.error(f"Error al conectar con Firebase: {str(e)}")
        st.stop()

firebase = init_firebase()

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
