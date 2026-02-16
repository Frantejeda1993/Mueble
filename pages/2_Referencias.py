import streamlit as st
import streamlit.components.v1 as components
from services.firebase_service import FirebaseService

# Inicializar Firebase
def get_firebase():
    """Obtiene la instancia de Firebase"""
    if 'firebase' not in st.session_state:
        try:
            with st.spinner("Conectando con Firebase..."):
                st.session_state.firebase = FirebaseService()
        except Exception as e:
            st.error("❌ Error conectando con Firebase")
            st.error(str(e))
            st.stop()
    return st.session_state.firebase

firebase = get_firebase()
st.session_state.active_nav_page = 'references'

st.title("📚 Referencias y Configuración")

components.html(
    """
    <script>
        window.onbeforeunload = function () {
            return 'Si tienes cambios sin guardar, se perderán. ¿Seguro que quieres salir?';
        };
    </script>
    """,
    height=0,
)


st.markdown("""
En esta sección puedes configurar:
- **Materiales**: Tipos de madera, colores, precios
- **Herrajes**: Bisagras, tiradores, guías, etc.
- **Servicio de Corte**: Precio y desperdicio
- **Logo**: Logo para los PDFs
""")

# Tabs
tabs = st.tabs(["🪵 Materiales", "🔩 Herrajes", "✂️ Servicio de Corte", "🖼️ Logo"])

# ========== TAB: MATERIALES ==========
with tabs[0]:
    st.subheader("Materiales")
    
    # Botón agregar
    if st.button("➕ Agregar Material"):
        try:
            new_material = {
                'type': 'Nuevo Material',
                'color': '',
                'thickness_mm': 18,
                'waste_factor': 0.10,
                'board_price': 0.0,
                'board_height_mm': 2440,
                'board_width_mm': 1220
            }
            firebase.create_material(new_material)
            st.success("Material agregado")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    # Listar materiales
    try:
        materials = firebase.get_all_materials()
        
        if not materials:
            st.info("No hay materiales registrados. Agrega el primero.")
        else:
            for material in materials:
                with st.expander(f"{material.get('type', '')} {material.get('color', '')} {material.get('thickness_mm', '')}mm"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        material['type'] = st.text_input(
                            "Tipo", 
                            material.get('type', ''), 
                            key=f"mat_type_{material['id']}"
                        )
                        
                        material['color'] = st.text_input(
                            "Color", 
                            material.get('color', ''), 
                            key=f"mat_color_{material['id']}"
                        )
                        
                        material['thickness_mm'] = st.number_input(
                            "Espesor (mm)", 
                            value=material.get('thickness_mm', 18), 
                            key=f"mat_thick_{material['id']}"
                        )
                        
                        material['waste_factor'] = st.number_input(
                            "Factor de desperdicio (0.10 = 10%)", 
                            value=material.get('waste_factor', 0.10),
                            min_value=0.0,
                            max_value=1.0,
                            step=0.01,
                            key=f"mat_waste_{material['id']}"
                        )
                    
                    with col2:
                        material['board_price'] = st.number_input(
                            "Precio por tabla (€)", 
                            value=material.get('board_price', 0.0),
                            key=f"mat_price_{material['id']}"
                        )
                        
                        material['board_height_mm'] = st.number_input(
                            "Alto de tabla (mm)", 
                            value=material.get('board_height_mm', 2440),
                            key=f"mat_height_{material['id']}"
                        )
                        
                        material['board_width_mm'] = st.number_input(
                            "Ancho de tabla (mm)", 
                            value=material.get('board_width_mm', 1220),
                            key=f"mat_width_{material['id']}"
                        )
                    
                    col_save, col_delete = st.columns([3, 1])
                    
                    with col_save:
                        if st.button("💾 Guardar", key=f"save_mat_{material['id']}", use_container_width=True):
                            try:
                                material_data = {
                                    'type': material['type'],
                                    'color': material['color'],
                                    'thickness_mm': material['thickness_mm'],
                                    'waste_factor': material['waste_factor'],
                                    'board_price': material['board_price'],
                                    'board_height_mm': material['board_height_mm'],
                                    'board_width_mm': material['board_width_mm']
                                }
                                firebase.update_material(material['id'], material_data)
                                st.success("✅ Material actualizado")
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                    
                    with col_delete:
                        confirm_key = f"confirm_delete_mat_{material['id']}"
                        if st.button("🗑️", key=f"del_mat_{material['id']}", use_container_width=True):
                            st.session_state[confirm_key] = True
                        if st.session_state.get(confirm_key):
                            st.warning("¿Eliminar este material?")
                            c1, c2 = st.columns(2)
                            with c1:
                                if st.button("Confirmar", key=f"ok_del_mat_{material['id']}"):
                                    try:
                                        firebase.delete_material(material['id'])
                                        st.session_state[confirm_key] = False
                                        st.success("Material eliminado")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
                            with c2:
                                if st.button("Cancelar", key=f"cancel_del_mat_{material['id']}"):
                                    st.session_state[confirm_key] = False
                                    st.rerun()
    
    except Exception as e:
        st.error(f"Error cargando materiales: {str(e)}")

# ========== TAB: HERRAJES ==========
with tabs[1]:
    st.subheader("Herrajes")
    
    # Botón agregar
    if st.button("➕ Agregar Herraje"):
        try:
            new_hardware = {
                'type': 'Nuevo Herraje',
                'price_unit': 0.0,
                'link': '',
                'image_url': ''
            }
            firebase.create_hardware(new_hardware)
            st.success("Herraje agregado")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    # Listar herrajes
    try:
        hardwares = firebase.get_all_hardware()
        
        if not hardwares:
            st.info("No hay herrajes registrados. Agrega el primero.")
        else:
            for hardware in hardwares:
                with st.expander(f"{hardware.get('type', '')} - {hardware.get('price_unit', 0):.2f}€"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        hardware['type'] = st.text_input(
                            "Tipo/Nombre", 
                            hardware.get('type', ''), 
                            key=f"hw_type_{hardware['id']}"
                        )
                        
                        hardware['price_unit'] = st.number_input(
                            "Precio unitario (€)", 
                            value=hardware.get('price_unit', 0.0),
                            key=f"hw_price_{hardware['id']}"
                        )
                    
                    with col2:
                        hardware['link'] = st.text_input(
                            "Link (opcional)", 
                            hardware.get('link', ''), 
                            key=f"hw_link_{hardware['id']}"
                        )
                        
                        hardware['image_url'] = st.text_input(
                            "URL imagen (opcional)", 
                            hardware.get('image_url', ''), 
                            key=f"hw_img_{hardware['id']}"
                        )
                    
                    # Mostrar imagen si existe
                    if hardware.get('image_url'):
                        try:
                            st.image(hardware['image_url'], width=200)
                        except:
                            pass
                    
                    col_save, col_delete = st.columns([3, 1])
                    
                    with col_save:
                        if st.button("💾 Guardar", key=f"save_hw_{hardware['id']}", use_container_width=True):
                            try:
                                hardware_data = {
                                    'type': hardware['type'],
                                    'price_unit': hardware['price_unit'],
                                    'link': hardware['link'],
                                    'image_url': hardware['image_url']
                                }
                                firebase.update_hardware(hardware['id'], hardware_data)
                                st.success("✅ Herraje actualizado")
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                    
                    with col_delete:
                        confirm_key = f"confirm_delete_hw_{hardware['id']}"
                        if st.button("🗑️", key=f"del_hw_{hardware['id']}", use_container_width=True):
                            st.session_state[confirm_key] = True
                        if st.session_state.get(confirm_key):
                            st.warning("¿Eliminar este herraje?")
                            c1, c2 = st.columns(2)
                            with c1:
                                if st.button("Confirmar", key=f"ok_del_hw_{hardware['id']}"):
                                    try:
                                        firebase.delete_hardware(hardware['id'])
                                        st.session_state[confirm_key] = False
                                        st.success("Herraje eliminado")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
                            with c2:
                                if st.button("Cancelar", key=f"cancel_del_hw_{hardware['id']}"):
                                    st.session_state[confirm_key] = False
                                    st.rerun()
    
    except Exception as e:
        st.error(f"Error cargando herrajes: {str(e)}")

# ========== TAB: SERVICIO DE CORTE ==========
with tabs[2]:
    st.subheader("Configuración del Servicio de Corte")
    
    try:
        cutting_service = firebase.get_cutting_service()
        
        col1, col2 = st.columns(2)
        
        with col1:
            price_per_m2 = st.number_input(
                "Precio por m² (€)",
                value=cutting_service.get('price_per_m2', 0.0),
                help="Precio del servicio de corte por metro cuadrado"
            )
        
        with col2:
            waste_factor = st.number_input(
                "Factor de desperdicio (0.10 = 10%)",
                value=cutting_service.get('waste_factor', 0.10),
                min_value=0.0,
                max_value=1.0,
                step=0.01,
                help="Desperdicio adicional para el servicio de corte"
            )
        
        if st.button("💾 Guardar Configuración", type="primary"):
            try:
                cutting_data = {
                    'price_per_m2': price_per_m2,
                    'waste_factor': waste_factor
                }
                firebase.update_cutting_service(cutting_data)
                st.success("✅ Configuración actualizada")
            except Exception as e:
                st.error(f"Error: {str(e)}")
        
        # Información adicional
        st.info("""
        **¿Cómo funciona el cálculo?**
        
        El costo de corte se calcula como:
        ```
        costo_corte = m² × precio_por_m² × (1 + factor_desperdicio)
        ```
        
        Por ejemplo:
        - Si tienes 10 m² de material
        - Precio: 5€/m²
        - Desperdicio: 10% (0.10)
        
        Resultado: 10 × 5 × 1.10 = 55€
        """)
    
    except Exception as e:
        st.error(f"Error cargando configuración: {str(e)}")

# ========== TAB: LOGO ==========
with tabs[3]:
    st.subheader("Logo para PDFs")
    
    st.markdown("""
    Sube un logo que se mostrará en los presupuestos PDF.
    
    **Recomendaciones:**
    - Formato: PNG con fondo transparente
    - Tamaño: 500x500 px o similar (cuadrado)
    - Peso: Máximo 1 MB
    """)
    
    # Mostrar logo actual si existe
    try:
        current_logo_base64 = firebase.get_logo_base64()
        if current_logo_base64:
            st.image(f"data:image/png;base64,{current_logo_base64}", width=200, caption="Logo actual")
    except:
        st.info("No hay logo configurado actualmente")
    
    # Subir nuevo logo
    uploaded_file = st.file_uploader("Subir nuevo logo", type=['png', 'jpg', 'jpeg'])
    
    if uploaded_file:
        # Mostrar preview
        st.image(uploaded_file, width=200, caption="Preview")
        
        if st.button("📤 Guardar Logo"):
            try:
                # Leer bytes del archivo
                file_bytes = uploaded_file.getvalue()
                
                # Verificar tamaño (máximo 1MB)
                if len(file_bytes) > 1_000_000:
                    st.error("El archivo es muy grande. Máximo 1 MB.")
                else:
                    # Guardar en Firestore
                    firebase.upload_logo(file_bytes)
                    
                    st.success("✅ Logo guardado correctamente")
                    st.rerun()
            except Exception as e:
                st.error(f"Error guardando logo: {str(e)}")
