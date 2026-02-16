import streamlit as st
from services.firebase_service import FirebaseService
from services.calculation_service import CalculationService
from services.pdf_service import PDFService
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Polygon

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


def save_project_data(firebase_service, project_id, project_name, project_client, project_date, project_status, project_data):
    """Guarda los datos actuales del proyecto"""
    payload = {
        'name': project_name,
        'client': project_client,
        'date': datetime.combine(project_date, datetime.min.time()),
        'status': project_status,
        'modules': project_data.get('modules', []),
        'shelves': project_data.get('shelves', []),
        'woods': project_data.get('woods', []),
        'hardwares': project_data.get('hardwares', []),
        'labor_cost_project': project_data.get('labor_cost_project', 0.0),
        'extra_complexity': project_data.get('extra_complexity', 0.0),
        'final_price': project_data.get('final_price', 0.0)
    }

    if project_id:
        firebase_service.update_project(project_id, payload)
        return project_id, "✅ Proyecto actualizado correctamente"

    new_id = firebase_service.create_project(payload)
    return new_id, "✅ Proyecto creado correctamente"


def draw_isometric_box(ax, x, y, width, height, depth, face_color='#ADD8E6', side_color='#8FB8D8', top_color='#C6E2F5'):
    """Dibuja una caja en vista isométrica"""
    dx = depth * 0.45
    dy = depth * 0.3

    front = Polygon(
        [(x, y), (x + width, y), (x + width, y + height), (x, y + height)],
        closed=True,
        facecolor=face_color,
        edgecolor='black',
        linewidth=1.5,
        alpha=0.8
    )
    side = Polygon(
        [
            (x + width, y),
            (x + width + dx, y + dy),
            (x + width + dx, y + height + dy),
            (x + width, y + height),
        ],
        closed=True,
        facecolor=side_color,
        edgecolor='black',
        linewidth=1.2,
        alpha=0.8
    )
    top = Polygon(
        [
            (x, y + height),
            (x + width, y + height),
            (x + width + dx, y + height + dy),
            (x + dx, y + height + dy),
        ],
        closed=True,
        facecolor=top_color,
        edgecolor='black',
        linewidth=1.2,
        alpha=0.8
    )

    ax.add_patch(front)
    ax.add_patch(side)
    ax.add_patch(top)

    return dx, dy


def format_dimensions(ancho_mm, alto_mm=None, profundo_mm=None):
    """Formatea dimensiones de forma consistente para todas las vistas."""
    if alto_mm is not None and profundo_mm is not None:
        return f"A {int(ancho_mm)} × H {int(alto_mm)} × P {int(profundo_mm)} mm"
    if profundo_mm is not None:
        return f"A {int(ancho_mm)} × P {int(profundo_mm)} mm"
    return f"A {int(ancho_mm)} mm"


def draw_module_structure(ax, x, y, width, height, depth, has_back=False, door_count=0):
    """Dibuja un módulo como estructura de 4 maderas, con fondo/puertas opcionales."""
    dx = depth * 0.35
    dy = depth * 0.22
    board_thickness = max(25, min(width, height) * 0.04)

    board_color = '#C49A6C'
    edge_color = '#5D4037'

    # Estructura frontal (4 maderas)
    ax.add_patch(patches.Rectangle((x, y), board_thickness, height, facecolor=board_color, edgecolor=edge_color, linewidth=1.2))
    ax.add_patch(patches.Rectangle((x + width - board_thickness, y), board_thickness, height, facecolor=board_color, edgecolor=edge_color, linewidth=1.2))
    ax.add_patch(patches.Rectangle((x, y + height - board_thickness), width, board_thickness, facecolor=board_color, edgecolor=edge_color, linewidth=1.2))
    ax.add_patch(patches.Rectangle((x, y), width, board_thickness, facecolor=board_color, edgecolor=edge_color, linewidth=1.2))

    # Aristas de profundidad para dar forma de cubo
    ax.plot([x, x + dx], [y + height, y + height + dy], color=edge_color, linewidth=1)
    ax.plot([x + width, x + width + dx], [y + height, y + height + dy], color=edge_color, linewidth=1)
    ax.plot([x + width, x + width + dx], [y, y + dy], color=edge_color, linewidth=1)

    ax.plot([x + dx, x + width + dx], [y + height + dy, y + height + dy], color=edge_color, linewidth=1)
    ax.plot([x + width + dx, x + width + dx], [y + dy, y + height + dy], color=edge_color, linewidth=1)
    ax.plot([x + width, x + width + dx], [y, y + dy], color=edge_color, linewidth=1)

    # Fondo (cara trasera tapada)
    if has_back:
        back = Polygon(
            [
                (x + dx, y + dy),
                (x + width + dx, y + dy),
                (x + width + dx, y + height + dy),
                (x + dx, y + height + dy),
            ],
            closed=True,
            facecolor='#E8D3B0',
            edgecolor=edge_color,
            linewidth=1,
            alpha=0.55
        )
        ax.add_patch(back)

    # Puertas (cara frontal tapada)
    if door_count > 0:
        if door_count >= 2:
            mid_x = x + width / 2
            ax.add_patch(patches.Rectangle((x, y), width / 2, height, facecolor='#DCEEFF', edgecolor='#3E6480', linewidth=1, alpha=0.45))
            ax.add_patch(patches.Rectangle((mid_x, y), width / 2, height, facecolor='#DCEEFF', edgecolor='#3E6480', linewidth=1, alpha=0.45))
            ax.plot([mid_x, mid_x], [y, y + height], color='#3E6480', linewidth=1.5)
        else:
            ax.add_patch(patches.Rectangle((x, y), width, height, facecolor='#DCEEFF', edgecolor='#3E6480', linewidth=1.2, alpha=0.45))

    return dx, dy

st.title("📁 Gestión de Proyectos")

# Modo de vista
if 'project_mode' not in st.session_state:
    st.session_state.project_mode = 'list'  # 'list' o 'edit'

if 'current_project_id' not in st.session_state:
    st.session_state.current_project_id = None

if st.session_state.get('active_nav_page') != 'projects':
    st.session_state.project_mode = 'list'

st.session_state.active_nav_page = 'projects'

# ========== VISTA LISTA ==========
if st.session_state.project_mode == 'list':
    
    # Filtros
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        search_name = st.text_input("🔍 Buscar por nombre", "")
    
    with col2:
        filter_status = st.selectbox("Estado", ["Todos", "Activo", "Cerrado"], index=1)
    
    with col3:
        if st.button("➕ Nuevo Proyecto", use_container_width=True):
            st.session_state.project_mode = 'edit'
            st.session_state.current_project_id = None
            st.session_state.edit_project = None
            st.session_state.edit_project_cache_id = None
            st.rerun()

    last_project_id = st.session_state.get('last_opened_project_id') or st.session_state.get('current_project_id')
    if last_project_id:
        if st.button("↩️ Volver al proyecto abierto", use_container_width=True):
            st.session_state.project_mode = 'edit'
            st.session_state.current_project_id = last_project_id
            st.session_state.edit_project = None
            st.session_state.edit_project_cache_id = None
            st.rerun()
    
    # Obtener proyectos
    try:
        projects = firebase.get_all_projects()
        
        # Aplicar filtros
        filtered_projects = projects
        
        if search_name:
            filtered_projects = [p for p in filtered_projects if search_name.lower() in p.get('name', '').lower()]
        
        if filter_status != "Todos":
            filtered_projects = [p for p in filtered_projects if p.get('status') == filter_status]
        
        # Mostrar proyectos
        st.markdown(f"### Proyectos encontrados: {len(filtered_projects)}")
        
        if not filtered_projects:
            st.info("No se encontraron proyectos con los filtros aplicados")
        else:
            for project in filtered_projects:
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{project.get('name', 'Sin nombre')}**")
                        st.caption(f"Cliente: {project.get('client', 'N/A')}")
                    
                    with col2:
                        date = project.get('date')
                        if isinstance(date, datetime):
                            st.text(date.strftime('%d/%m/%Y'))
                        else:
                            st.text("N/A")
                    
                    with col3:
                        status = project.get('status', 'Activo')
                        if status == 'Activo':
                            st.success(status)
                        else:
                            st.info(status)
                    
                    with col4:
                        if st.button("Abrir", key=f"open_{project['id']}", use_container_width=True):
                            st.session_state.project_mode = 'edit'
                            st.session_state.current_project_id = project['id']
                            st.session_state.last_opened_project_id = project['id']
                            st.session_state.edit_project = None
                            st.session_state.edit_project_cache_id = None
                            st.rerun()
                    
                    st.divider()
    
    except Exception as e:
        st.error(f"Error cargando proyectos: {str(e)}")

# ========== VISTA EDICIÓN ==========
elif st.session_state.project_mode == 'edit':
    
    # Botón volver
    if st.button("← Volver a lista"):
        st.session_state.project_mode = 'list'
        st.session_state.edit_project = None
        st.session_state.edit_project_cache_id = None
        st.rerun()
    
    st.markdown("---")
    
    # Cargar proyecto editable en session_state para no perder cambios en cada recarga
    current_id = st.session_state.current_project_id
    cache_id = current_id if current_id else '__new__'

    if st.session_state.get('edit_project_cache_id') != cache_id or 'edit_project' not in st.session_state:
        if current_id:
            try:
                loaded_project = firebase.get_project(current_id)
                if not loaded_project:
                    st.error("Proyecto no encontrado")
                    st.stop()
            except Exception as e:
                st.error(f"Error cargando proyecto: {str(e)}")
                st.stop()
        else:
            loaded_project = {
                'name': '',
                'client': '',
                'date': datetime.now(),
                'status': 'Activo',
                'modules': [],
                'shelves': [],
                'woods': [],
                'hardwares': [],
                'labor_cost_project': 0.0,
                'extra_complexity': 0.0,
                'final_price': 0.0
            }

        st.session_state.edit_project = loaded_project
        st.session_state.edit_project_cache_id = cache_id

    project = st.session_state.edit_project
    
    # Información básica
    st.subheader("Información del Proyecto")
    
    col1, col2 = st.columns(2)
    with col1:
        project_name = st.text_input("Nombre del proyecto", project.get('name', ''))
        project_client = st.text_input("Cliente", project.get('client', ''))
    
    with col2:
        project_date = st.date_input("Fecha", project.get('date', datetime.now()))
        project_status = st.selectbox("Estado", ["Activo", "Cerrado"], 
                                     index=0 if project.get('status') == 'Activo' else 1)

    # Mantener borrador sincronizado con datos básicos
    project['name'] = project_name
    project['client'] = project_client
    project['date'] = datetime.combine(project_date, datetime.min.time())
    project['status'] = project_status
    
    # Botón guardar
    col_save, col_delete = st.columns([3, 1])
    with col_save:
        if st.button("💾 Guardar Proyecto", type="primary", use_container_width=True):
            try:
                current_id, success_msg = save_project_data(
                    firebase,
                    st.session_state.current_project_id,
                    project_name,
                    project_client,
                    project_date,
                    project_status,
                    project
                )
                st.session_state.current_project_id = current_id
                st.session_state.last_opened_project_id = current_id
                st.session_state.edit_project_cache_id = current_id
                st.success(success_msg)
                if "creado" in success_msg:
                    st.rerun()
            except Exception as e:
                st.error(f"Error guardando proyecto: {str(e)}")
    
    with col_delete:
        if st.session_state.current_project_id:
            if st.button("🗑️ Eliminar", use_container_width=True):
                try:
                    firebase.delete_project(st.session_state.current_project_id)
                    st.success("Proyecto eliminado")
                    st.session_state.project_mode = 'list'
                    st.session_state.current_project_id = None
                    st.session_state.edit_project = None
                    st.session_state.edit_project_cache_id = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Error eliminando: {str(e)}")
    
    st.markdown("---")
    
    # Tabs para las secciones
    tabs = st.tabs(["📦 Módulos", "📏 Estantes", "🪵 Maderas", "🔩 Herrajes", "💰 Costos", "📊 Vista Gráfica", "📄 PDF"])
    
    # TAB: MÓDULOS
    with tabs[0]:
        st.subheader("Módulos")
        
        # Obtener materiales
        try:
            materials_list = firebase.get_all_materials()
            materials_dict = {f"{m['type']}_{m.get('color', '')}_{m.get('thickness_mm', 0)}": m for m in materials_list}
            material_options = list(materials_dict.keys())
            material_labels = {
                key: f"{m['type']} {m.get('color', '')} {m.get('thickness_mm', '')}mm".strip()
                for key, m in materials_dict.items()
            }
        except:
            material_options = []
            materials_dict = {}
            material_labels = {}
        
        if st.button("➕ Agregar Módulo"):
            if 'modules' not in project:
                project['modules'] = []
            project['modules'].append({
                'nombre': f'Módulo {len(project["modules"]) + 1}',
                'alto_mm': 2000,
                'ancho_mm': 1000,
                'profundo_mm': 400,
                'material': '',
                'material_fondo': '',
                'tiene_fondo': False,
                'tiene_puertas': False,
                'cantidad_puertas': 0,
                'cantidad_estantes': 0,
                'cantidad_divisiones': 0
            })
        
        for idx, module in enumerate(project.get('modules', [])):
            with st.expander(f"Módulo {idx + 1}: {module.get('nombre', '')}"):
                col1, col2 = st.columns(2)

                with col1:
                    module['nombre'] = st.text_input("Nombre", module.get('nombre', ''), key=f"mod_name_{idx}")
                    module['alto_mm'] = st.number_input("Alto (mm)", value=module.get('alto_mm', 2000), key=f"mod_alto_{idx}")
                    module['ancho_mm'] = st.number_input("Ancho (mm)", value=module.get('ancho_mm', 1000), key=f"mod_ancho_{idx}")
                    module['profundo_mm'] = st.number_input("Profundidad (mm)", value=module.get('profundo_mm', 400), key=f"mod_prof_{idx}")

                with col2:
                    material_value = module.get('material', '')
                    if material_options:
                        default_index = material_options.index(material_value) if material_value in material_options else 0
                        module['material'] = st.selectbox(
                            "Material",
                            material_options,
                            index=default_index,
                            format_func=lambda x: material_labels.get(x, x),
                            key=f"mod_mat_{idx}"
                        )

                    module['tiene_fondo'] = st.checkbox("Tiene fondo", module.get('tiene_fondo', False), key=f"mod_fondo_{idx}")

                    material_fondo = module.get('material_fondo', module.get('material', ''))
                    if module['tiene_fondo'] and material_options:
                        back_default_index = material_options.index(material_fondo) if material_fondo in material_options else 0
                        module['material_fondo'] = st.selectbox(
                            "Material fondo",
                            material_options,
                            index=back_default_index,
                            format_func=lambda x: material_labels.get(x, x),
                            key=f"mod_back_mat_{idx}"
                        )
                    else:
                        module['material_fondo'] = ''

                    module['tiene_puertas'] = st.checkbox("Tiene puertas", module.get('tiene_puertas', False), key=f"mod_puertas_{idx}")

                    if module['tiene_puertas']:
                        module['cantidad_puertas'] = st.number_input(
                            "Cantidad puertas",
                            value=module.get('cantidad_puertas', 1),
                            min_value=0,
                            key=f"mod_cant_puertas_{idx}"
                        )
                    else:
                        module['cantidad_puertas'] = 0

                    module['cantidad_estantes'] = st.number_input("Cantidad estantes", value=module.get('cantidad_estantes', 0), min_value=0, key=f"mod_est_{idx}")
                    module['cantidad_divisiones'] = st.number_input("Cantidad divisiones", value=module.get('cantidad_divisiones', 0), min_value=0, key=f"mod_div_{idx}")

                if st.button(f"🗑️ Eliminar módulo {idx + 1}", key=f"del_mod_{idx}"):
                    project['modules'].pop(idx)
                    st.rerun()

        if st.button("💾 Guardar cambios de módulos", key="save_modules", type="primary", use_container_width=True):
            try:
                current_id, success_msg = save_project_data(
                    firebase,
                    st.session_state.current_project_id,
                    project_name,
                    project_client,
                    project_date,
                    project_status,
                    project
                )
                st.session_state.current_project_id = current_id
                st.session_state.last_opened_project_id = current_id
                st.session_state.edit_project_cache_id = current_id
                st.success(success_msg)
            except Exception as e:
                st.error(f"Error guardando cambios de módulos: {str(e)}")
    
    # TAB: ESTANTES
    with tabs[1]:
        st.subheader("Estantes Independientes")
        
        if st.button("➕ Agregar Estante"):
            if 'shelves' not in project:
                project['shelves'] = []
            project['shelves'].append({
                'nombre': f'Estante {len(project["shelves"]) + 1}',
                'ancho_mm': 800,
                'profundo_mm': 300,
                'cantidad': 1,
                'material': ''
            })
        
        for idx, shelf in enumerate(project.get('shelves', [])):
            with st.expander(f"Estante {idx + 1}: {shelf.get('nombre', '')}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    shelf['nombre'] = st.text_input("Nombre", shelf.get('nombre', ''), key=f"shelf_name_{idx}")
                    shelf['ancho_mm'] = st.number_input("Ancho (mm)", value=shelf.get('ancho_mm', 800), key=f"shelf_ancho_{idx}")
                
                with col2:
                    shelf['profundo_mm'] = st.number_input("Profundidad (mm)", value=shelf.get('profundo_mm', 300), key=f"shelf_prof_{idx}")
                    shelf['cantidad'] = st.number_input("Cantidad", value=shelf.get('cantidad', 1), min_value=1, key=f"shelf_cant_{idx}")
                
                if material_options:
                    material_value = shelf.get('material', '')
                    default_index = material_options.index(material_value) if material_value in material_options else 0
                    shelf['material'] = st.selectbox(
                        "Material",
                        material_options,
                        index=default_index,
                        format_func=lambda x: material_labels.get(x, x),
                        key=f"shelf_mat_{idx}"
                    )
                
                if st.button(f"🗑️ Eliminar estante {idx + 1}", key=f"del_shelf_{idx}"):
                    project['shelves'].pop(idx)
                    st.rerun()

        if st.button("💾 Guardar cambios de estantes", key="save_shelves", use_container_width=True):
            try:
                current_id, success_msg = save_project_data(
                    firebase,
                    st.session_state.current_project_id,
                    project_name,
                    project_client,
                    project_date,
                    project_status,
                    project
                )
                st.session_state.current_project_id = current_id
                st.session_state.last_opened_project_id = current_id
                st.session_state.edit_project_cache_id = current_id
                st.success(success_msg)
            except Exception as e:
                st.error(f"Error guardando cambios de estantes: {str(e)}")
    
    # TAB: MADERAS
    with tabs[2]:
        st.subheader("Maderas Independientes")
        
        if st.button("➕ Agregar Madera"):
            if 'woods' not in project:
                project['woods'] = []
            project['woods'].append({
                'nombre': f'Madera {len(project["woods"]) + 1}',
                'ancho_mm': 500,
                'profundo_mm': 200,
                'cantidad': 1,
                'material': ''
            })
        
        for idx, wood in enumerate(project.get('woods', [])):
            with st.expander(f"Madera {idx + 1}: {wood.get('nombre', '')}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    wood['nombre'] = st.text_input("Nombre", wood.get('nombre', ''), key=f"wood_name_{idx}")
                    wood['ancho_mm'] = st.number_input("Ancho (mm)", value=wood.get('ancho_mm', 500), key=f"wood_ancho_{idx}")
                
                with col2:
                    wood['profundo_mm'] = st.number_input("Profundidad (mm)", value=wood.get('profundo_mm', 200), key=f"wood_prof_{idx}")
                    wood['cantidad'] = st.number_input("Cantidad", value=wood.get('cantidad', 1), min_value=1, key=f"wood_cant_{idx}")
                
                if material_options:
                    material_value = wood.get('material', '')
                    default_index = material_options.index(material_value) if material_value in material_options else 0
                    wood['material'] = st.selectbox(
                        "Material",
                        material_options,
                        index=default_index,
                        format_func=lambda x: material_labels.get(x, x),
                        key=f"wood_mat_{idx}"
                    )
                
                if st.button(f"🗑️ Eliminar madera {idx + 1}", key=f"del_wood_{idx}"):
                    project['woods'].pop(idx)
                    st.rerun()

        if st.button("💾 Guardar cambios de maderas", key="save_woods", use_container_width=True):
            try:
                current_id, success_msg = save_project_data(
                    firebase,
                    st.session_state.current_project_id,
                    project_name,
                    project_client,
                    project_date,
                    project_status,
                    project
                )
                st.session_state.current_project_id = current_id
                st.session_state.last_opened_project_id = current_id
                st.session_state.edit_project_cache_id = current_id
                st.success(success_msg)
            except Exception as e:
                st.error(f"Error guardando cambios de maderas: {str(e)}")
    
    # TAB: HERRAJES
    with tabs[3]:
        st.subheader("Herrajes")
        
        # Obtener herrajes de BD
        try:
            hardware_list = firebase.get_all_hardware()
            hardware_options = ["Personalizado"] + [h['type'] for h in hardware_list]
            hardware_dict = {h['type']: h for h in hardware_list}
        except:
            hardware_options = ["Personalizado"]
            hardware_dict = {}
        
        if st.button("➕ Agregar Herraje"):
            if 'hardwares' not in project:
                project['hardwares'] = []
            project['hardwares'].append({
                'type': 'Herraje',
                'quantity': 1,
                'price_unit': 0.0
            })
        
        for idx, hardware in enumerate(project.get('hardwares', [])):
            with st.expander(f"Herraje {idx + 1}: {hardware.get('type', '')}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    current_hw_type = hardware.get('type', '')
                    default_hw = current_hw_type if current_hw_type in hardware_dict else "Personalizado"
                    default_index = hardware_options.index(default_hw) if default_hw in hardware_options else 0
                    selected_hw = st.selectbox("Tipo", hardware_options, index=default_index, key=f"hw_type_{idx}")

                    is_custom_hardware = selected_hw == "Personalizado"
                    if is_custom_hardware:
                        hardware['type'] = st.text_input("Nombre personalizado", current_hw_type, key=f"hw_custom_{idx}")
                    else:
                        hardware['type'] = selected_hw
                        if selected_hw in hardware_dict:
                            hardware['price_unit'] = hardware_dict[selected_hw].get('price_unit', 0.0)
                
                with col2:
                    hardware['quantity'] = st.number_input("Cantidad", value=hardware.get('quantity', 1), min_value=0, key=f"hw_qty_{idx}")
                
                with col3:
                    if is_custom_hardware:
                        hardware['price_unit'] = st.number_input(
                            "Precio unitario (€)",
                            value=hardware.get('price_unit', 0.0),
                            key=f"hw_price_custom_{idx}",
                            help="Solo editable para herrajes personalizados"
                        )
                    else:
                        selected_price = hardware_dict.get(selected_hw, {}).get('price_unit', 0.0)
                        hardware['price_unit'] = selected_price
                        st.number_input(
                            "Precio unitario (€)",
                            value=float(selected_price),
                            key=f"hw_price_ref_{idx}_{selected_hw}",
                            disabled=True,
                            help="Tomado automáticamente de Referencias > Herrajes"
                        )
                
                if st.button(f"🗑️ Eliminar herraje {idx + 1}", key=f"del_hw_{idx}"):
                    project['hardwares'].pop(idx)
                    st.rerun()

        if st.button("💾 Guardar cambios de herrajes", key="save_hardwares", use_container_width=True):
            try:
                current_id, success_msg = save_project_data(
                    firebase,
                    st.session_state.current_project_id,
                    project_name,
                    project_client,
                    project_date,
                    project_status,
                    project
                )
                st.session_state.current_project_id = current_id
                st.session_state.last_opened_project_id = current_id
                st.session_state.edit_project_cache_id = current_id
                st.success(success_msg)
            except Exception as e:
                st.error(f"Error guardando cambios de herrajes: {str(e)}")
    
    # TAB: COSTOS
    with tabs[4]:
        st.subheader("💰 Costos Adicionales")
        
        col1, col2 = st.columns(2)
        
        with col1:
            project['labor_cost_project'] = st.number_input(
                "Mano de obra proyecto (€)",
                value=project.get('labor_cost_project', 0.0),
                help="Costo base de mano de obra"
            )
        
        with col2:
            project['extra_complexity'] = st.number_input(
                "Complejidad extra (€)",
                value=project.get('extra_complexity', 0.0),
                help="Costo adicional por complejidad"
            )
        
        st.markdown("---")
        
        # Calcular totales
        try:
            materials_db_list = firebase.get_all_materials()
            cutting_service = firebase.get_cutting_service()
            
            calculations = CalculationService.calculate_all_project_costs(
                project,
                materials_db_list,
                cutting_service
            )
            
            st.subheader("📊 Resumen de Costos")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                material_total = sum(c['material_cost'] for c in calculations['material_costs'].values())
                st.metric("Materiales", f"{material_total:.2f} €")
            
            with col2:
                st.metric("Corte y canto", f"{calculations['cutting_cost']:.2f} €")
            
            with col3:
                st.metric("Herrajes", f"{calculations['hardware_total']:.2f} €")
            
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Calculado", f"{calculations['total_calculated']:.2f} €", 
                         help="Suma automática de todos los costos")
            
            with col2:
                project['final_price'] = st.number_input(
                    "Precio Final (€)",
                    value=project.get('final_price', calculations['total_calculated']),
                    help="Precio editable que se mostrará al cliente"
                )
            
            st.info(f"💼 Mano de obra en PDF: {calculations['labor_for_invoice']:.2f} €")
            
        except Exception as e:
            st.error(f"Error calculando costos: {str(e)}")
    
    # TAB: VISTA GRÁFICA
    with tabs[5]:
        st.subheader("📊 Vista Gráfica")
        
        # Dibujar cada módulo por separado
        if project.get('modules'):
            st.markdown("### Módulos")

            for idx, module in enumerate(project['modules']):
                alto = module.get('alto_mm', 2000)
                ancho = module.get('ancho_mm', 1000)
                profundo = module.get('profundo_mm', 400)
                fig, ax = plt.subplots(figsize=(7, 4))

                puertas = module.get('cantidad_puertas', 0) if module.get('tiene_puertas') else 0
                draw_module_structure(
                    ax,
                    0,
                    0,
                    ancho,
                    alto,
                    profundo,
                    has_back=module.get('tiene_fondo', False),
                    door_count=puertas
                )

                estantes = module.get('cantidad_estantes', 0)
                if estantes > 0:
                    spacing = alto / (estantes + 1)
                    for i in range(1, estantes + 1):
                        y_pos = i * spacing
                        ax.plot([25, ancho - 25], [y_pos, y_pos], linestyle='--', color='#C62828', linewidth=1)

                divisiones = module.get('cantidad_divisiones', 0)
                if divisiones > 0:
                    spacing = ancho / (divisiones + 1)
                    for i in range(1, divisiones + 1):
                        x_pos = i * spacing
                        ax.plot([x_pos, x_pos], [25, alto - 25], linestyle='--', color='#2E7D32', linewidth=1)

                label = module.get('nombre', f'Módulo {idx + 1}')
                dim_label = format_dimensions(ancho, alto, profundo)
                if module.get('tiene_fondo'):
                    dim_label += " • Fondo"
                if puertas > 0:
                    dim_label += f" • {puertas} puerta(s)"

                st.caption(f"{label} — {dim_label}")

                ax.set_xlim(-80, ancho + (profundo * 0.35) + 120)
                ax.set_ylim(-alto * 0.18, alto + (profundo * 0.35) + 60)
                ax.set_aspect('equal')
                ax.axis('off')

                st.pyplot(fig)
                plt.close()

        # Dibujar estantes agrupados por medida
        if project.get('shelves'):
            st.markdown("### Estantes Independientes")

            grouped_shelves = {}
            for shelf in project['shelves']:
                key = (shelf.get('ancho_mm', 800), shelf.get('profundo_mm', 300))
                grouped_shelves[key] = grouped_shelves.get(key, 0) + max(1, int(shelf.get('cantidad', 1)))

            groups = list(grouped_shelves.items())
            max_prof = max([dims[1] for dims, _ in groups])
            max_qty = max([qty for _, qty in groups])
            fig, ax = plt.subplots(figsize=(max(7, min(14, len(groups) * 2.2)), max(3.2, 2.4 + (max_qty - 1) * 0.7)))

            x_cursor = 0
            shelf_height = 45
            stack_gap = 70

            for (ancho, profundo), qty in groups:
                dx = profundo * 0.45
                for level in range(qty):
                    y_pos = level * stack_gap
                    draw_isometric_box(
                        ax,
                        x_cursor,
                        y_pos,
                        ancho,
                        shelf_height,
                        profundo,
                        face_color='wheat',
                        side_color='#D2B48C',
                        top_color='#F5DEB3'
                    )

                dim_text = format_dimensions(ancho, profundo_mm=profundo)
                if qty > 1:
                    dim_text += f" (x{qty})"
                ax.text(x_cursor + ancho / 2, -90, dim_text, ha='center', va='top', fontsize=7)
                x_cursor += ancho + dx + max(140, ancho * 0.2)

            ax.set_xlim(-50, x_cursor)
            ax.set_ylim(-120, (max_qty - 1) * stack_gap + shelf_height + (max_prof * 0.4) + 60)
            ax.set_aspect('equal')
            ax.axis('off')

            st.pyplot(fig)
            plt.close()

        # Dibujar maderas agrupadas por medida
        if project.get('woods'):
            st.markdown("### Maderas Independientes")

            grouped_woods = {}
            for wood in project['woods']:
                key = (wood.get('ancho_mm', 500), wood.get('profundo_mm', 200))
                grouped_woods[key] = grouped_woods.get(key, 0) + max(1, int(wood.get('cantidad', 1)))

            groups = list(grouped_woods.items())
            max_qty = max([qty for _, qty in groups])
            max_prof = max([dims[1] for dims, _ in groups])
            fig, ax = plt.subplots(figsize=(max(7, min(14, len(groups) * 2.0)), max(3.0, 2.2 + (max_qty - 1) * 0.65)))

            x_cursor = 0
            wood_height = 40
            stack_gap = 62

            for (ancho, profundo), qty in groups:
                for level in range(qty):
                    y_pos = level * stack_gap
                    rect = patches.Rectangle(
                        (x_cursor, y_pos),
                        ancho,
                        wood_height,
                        linewidth=1.2,
                        edgecolor='saddlebrown',
                        facecolor='burlywood',
                        alpha=0.75
                    )
                    ax.add_patch(rect)

                dim_text = format_dimensions(ancho, profundo_mm=profundo)
                if qty > 1:
                    dim_text += f" (x{qty})"
                ax.text(x_cursor + ancho / 2, -75, dim_text, ha='center', va='top', fontsize=7)
                x_cursor += ancho + max(135, ancho * 0.2)

            ax.set_xlim(-50, x_cursor)
            ax.set_ylim(-105, (max_qty - 1) * stack_gap + wood_height + (max_prof * 0.05) + 50)
            ax.set_aspect('equal')
            ax.axis('off')

            st.pyplot(fig)
            plt.close()
    
    # TAB: PDF
    with tabs[6]:
        st.subheader("📄 Generar PDF")
        
        if st.button("📥 Descargar PDF", type="primary"):
            try:
                # Calcular costos
                materials_db_list = firebase.get_all_materials()
                cutting_service = firebase.get_cutting_service()
                
                materials_dict_for_pdf = {
                    f"{m['type']}_{m.get('color', '')}_{m.get('thickness_mm', 0)}": m 
                    for m in materials_db_list
                }
                
                calculations = CalculationService.calculate_all_project_costs(
                    project,
                    materials_db_list,
                    cutting_service
                )
                
                # Obtener logo (ahora en base64)
                logo_base64 = firebase.get_logo_base64()
                
                # Generar PDF
                pdf_buffer = PDFService.generate_pdf(
                    project,
                    calculations,
                    materials_dict_for_pdf,
                    logo_base64
                )
                
                # Descargar
                st.download_button(
                    label="⬇️ Descargar PDF",
                    data=pdf_buffer,
                    file_name=f"Presupuesto_{project_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf"
                )
                
                st.success("✅ PDF generado correctamente")
                
            except Exception as e:
                st.error(f"Error generando PDF: {str(e)}")
