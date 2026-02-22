import copy
import json

import streamlit as st
import streamlit.components.v1 as components
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



HARDWARE_CATEGORY_OPTIONS = ["Bisagra", "Corredera", "Item general"]


def normalize_hardware_category(hardware):
    category = hardware.get('category', 'Item general')
    if category not in HARDWARE_CATEGORY_OPTIONS:
        return 'Item general'
    return category


def get_hardware_catalog_by_category(firebase_service, allowed_categories=None):
    try:
        hardware_list = firebase_service.get_all_hardware()
    except Exception:
        return [], {}

    filtered = []
    for hardware in hardware_list:
        category = normalize_hardware_category(hardware)
        if allowed_categories and category not in allowed_categories:
            continue
        item = {**hardware, 'category': category}
        filtered.append(item)

    catalog = {h['type']: h for h in filtered if h.get('type')}
    return filtered, catalog


def get_default_drawer_config(base_material=''):
    return {
        'enabled': False,
        'tipo': 'Magic',
        'ancho_mm': 0,
        'alto_mm': 150,
        'profundo_mm': 0,
        'cantidad_cajones': 0,
        'material': base_material,
        'corredera': {
            'type': 'Personalizado',
            'category': 'Corredera',
            'price_unit': 0.0
        }
    }


def build_material_summary_rows(calculations, materials_db_list):
    """Construye filas para resumir m2, tablas y valor por madera."""
    materials_by_key = {
        f"{mat['type']}_{mat.get('color', '')}_{mat.get('thickness_mm', 0)}": mat
        for mat in materials_db_list
    }

    rows = []
    for material_key, m2_total in calculations.get('material_totals', {}).items():
        cost_data = calculations.get('material_costs', {}).get(material_key, {})
        material_info = materials_by_key.get(material_key, {})

        rows.append({
            'Madera': material_info.get('type', material_key),
            'Color': material_info.get('color', '-'),
            'Espesor (mm)': material_info.get('thickness_mm', '-'),
            'm² utilizados': round(m2_total, 3),
            'Tablas equivalentes': cost_data.get('boards_needed', 0),
            'Valor (€)': round(cost_data.get('material_cost', 0.0), 2)
        })

    return rows


def build_material_origin_details(project, material_key):
    """Construye detalle de origen por madera para mostrar en acordeón."""
    rows = []

    for module in project.get('modules', []):
        if module.get('material') == material_key:
            qty = max(1, int(module.get('cantidad_modulos', 1)))
            m2 = CalculationService.mm_to_m2(module.get('alto_mm', 0), module.get('profundo_mm', 0)) * 2
            m2 += CalculationService.mm_to_m2(module.get('ancho_mm', 0), module.get('profundo_mm', 0)) * 2
            rows.append({
                'Nombre': module.get('nombre', 'Módulo'),
                'Tipo': 'Modulo',
                'Medidas': f"{module.get('ancho_mm', 0)}x{module.get('alto_mm', 0)}x{module.get('profundo_mm', 0)} mm",
                'Metros cuadrados': round(m2 * qty, 3)
            })

    for shelf in project.get('shelves', []):
        if shelf.get('material') == material_key:
            qty = max(1, int(shelf.get('cantidad', 1)))
            m2 = CalculationService.mm_to_m2(shelf.get('ancho_mm', 0), shelf.get('profundo_mm', 0)) * qty
            rows.append({
                'Nombre': shelf.get('nombre', 'Estante'),
                'Tipo': 'estante',
                'Medidas': f"{shelf.get('ancho_mm', 0)}x{shelf.get('profundo_mm', 0)} mm",
                'Metros cuadrados': round(m2, 3)
            })

    for wood in project.get('woods', []):
        if wood.get('material') == material_key:
            qty = max(1, int(wood.get('cantidad', 1)))
            m2 = CalculationService.mm_to_m2(wood.get('ancho_mm', 0), wood.get('profundo_mm', 0)) * qty
            rows.append({
                'Nombre': wood.get('nombre', 'Madera'),
                'Tipo': 'Maderas',
                'Medidas': f"{wood.get('ancho_mm', 0)}x{wood.get('profundo_mm', 0)} mm",
                'Metros cuadrados': round(m2, 3)
            })

    return rows


def build_hardware_summary_rows(project):
    """Construye filas para resumir tipo, cantidad y precios de herrajes usados."""
    grouped = {}

    def add_hardware_item(item, multiplier=1, default_name='Herraje'):
        hardware_type = item.get('type', default_name)
        unit_price = float(item.get('price_unit', 0.0) or 0.0)
        quantity = float(item.get('quantity', 0) or 0) * multiplier

        if quantity <= 0:
            return

        key = (hardware_type, unit_price)
        if key not in grouped:
            grouped[key] = {
                'Tipo': hardware_type,
                'Cantidad': 0,
                'Precio unitario (€)': unit_price,
                'Subtotal (€)': 0.0
            }

        grouped[key]['Cantidad'] += quantity
        grouped[key]['Subtotal (€)'] += quantity * unit_price

    for hardware in project.get('hardwares', []):
        add_hardware_item(hardware)

    for module in project.get('modules', []):
        module_multiplier = max(1, int(module.get('cantidad_modulos', 1)))

        for hardware in module.get('herrajes', []):
            add_hardware_item(hardware, multiplier=module_multiplier)

        drawer_config = module.get('cajones', {})
        if drawer_config and drawer_config.get('enabled', False):
            drawer_qty = max(1, int(drawer_config.get('cantidad_cajones', 1)))
            slide = drawer_config.get('corredera')
            if slide:
                slide_quantity = slide.get('quantity', drawer_qty)
                slide_with_quantity = {**slide, 'quantity': slide_quantity}
                add_hardware_item(slide_with_quantity, multiplier=module_multiplier, default_name='Corredera cajón')

            for hinge in drawer_config.get('bisagras', []):
                add_hardware_item(hinge, multiplier=module_multiplier)

    rows = []
    for summary in grouped.values():
        summary['Cantidad'] = int(summary['Cantidad']) if float(summary['Cantidad']).is_integer() else round(summary['Cantidad'], 2)
        summary['Precio unitario (€)'] = round(summary['Precio unitario (€)'], 2)
        summary['Subtotal (€)'] = round(summary['Subtotal (€)'], 2)
        rows.append(summary)

    rows.sort(key=lambda row: row['Tipo'])
    return rows



def get_economy_movements_safe(firebase_service):
    if hasattr(firebase_service, 'get_economy_movements'):
        return firebase_service.get_economy_movements()
    rows = []
    docs = firebase_service.db.collection('economia_movimientos').stream(timeout=20.0)
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        rows.append(data)
    return sorted(rows, key=lambda x: x.get('fecha') or datetime.min, reverse=True)


def get_all_employees_safe(firebase_service):
    if hasattr(firebase_service, 'get_all_employees'):
        return firebase_service.get_all_employees()
    rows = []
    docs = firebase_service.db.collection('referencias').document('empleados').collection('items').stream(timeout=15.0)
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        rows.append(data)
    return rows

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


def _normalize_project_for_compare(project_data):
    """Normaliza datos para comparar cambios sin falsos positivos."""
    normalized = copy.deepcopy(project_data)
    date_value = normalized.get('date')
    if hasattr(date_value, 'date'):
        normalized['date'] = date_value.date().isoformat()
    elif date_value is not None:
        normalized['date'] = str(date_value)
    return normalized


def serialize_project_state(project_data):
    """Serializa el proyecto para comparar cambios pendientes de guardado."""
    normalized = _normalize_project_for_compare(project_data)
    return json.dumps(normalized, sort_keys=True, default=str)


def enable_unsaved_changes_guard(enabled):
    """Controla la alerta nativa solo para cierres reales de pestaña.

    En Streamlit, `onbeforeunload` se dispara también al hacer clic en botones
    (porque la app se recarga), por eso se desactiva para evitar falsos positivos.
    """
    components.html("<script>window.onbeforeunload = null;</script>", height=0)


def draw_dimension_labels(ax, x, y, width, height, depth, dx, dy):
    """Imprime medidas sobre el lado correspondiente del módulo."""
    dim_style = dict(fontsize=8, color='#1B263B', fontweight='bold')

    # Ancho en el frente inferior (más separado del dibujo)
    ax.annotate('', xy=(x, y - 68), xytext=(x + width, y - 68),
                arrowprops=dict(arrowstyle='<->', color='#1B263B', lw=1))
    ax.text(x + width / 2, y - 82, f"A {int(width)} mm", ha='center', va='top', **dim_style)

    # Alto en lateral izquierdo (más separado)
    ax.annotate('', xy=(x - 68, y), xytext=(x - 68, y + height),
                arrowprops=dict(arrowstyle='<->', color='#1B263B', lw=1))
    ax.text(x - 84, y + height / 2, f"H {int(height)} mm", ha='right', va='center', rotation=90, **dim_style)

    # Profundidad desplazada fuera de la arista para no ensuciar
    ax.annotate('', xy=(x + width + 14, y + height + 14), xytext=(x + width + dx + 22, y + height + dy + 22),
                arrowprops=dict(arrowstyle='<->', color='#1B263B', lw=1))
    ax.text(x + width + (dx / 2) + 30, y + height + (dy / 2) + 28, f"P {int(depth)} mm",
            ha='left', va='bottom', rotation=25, **dim_style)


def prepare_grouped_items(items, default_name):
    """Prepara piezas agrupadas por item: cantidad apilada, items distintos en columnas."""
    grouped = []
    for idx, item in enumerate(items):
        grouped.append({
            'nombre': item.get('nombre') or f"{default_name} {idx + 1}",
            'ancho_mm': item.get('ancho_mm', 0),
            'profundo_mm': item.get('profundo_mm', 0),
            'cantidad': max(1, int(item.get('cantidad', 1)))
        })
    return grouped


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
    if alto_mm is not None:
        return f"A {int(ancho_mm)} × H {int(alto_mm)} mm"
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


def draw_module_drawers(ax, x, y, width, height, drawer_qty):
    """Dibuja cajones en el frente del módulo cuando corresponda."""
    if drawer_qty <= 0:
        return

    qty = max(1, int(drawer_qty))
    usable_height = height * 0.86
    start_y = y + (height - usable_height) / 2
    drawer_height = usable_height / qty
    side_margin = max(16, width * 0.06)
    front_width = max(40, width - (2 * side_margin))

    for index in range(qty):
        drawer_y = start_y + (index * drawer_height) + (drawer_height * 0.08)
        front_height = drawer_height * 0.76

        ax.add_patch(
            patches.Rectangle(
                (x + side_margin, drawer_y),
                front_width,
                front_height,
                facecolor='#F8E7D2',
                edgecolor='#7A4E2F',
                linewidth=1.2,
                alpha=0.9
            )
        )

        handle_w = min(80, front_width * 0.24)
        handle_h = max(4, front_height * 0.08)
        handle_x = x + side_margin + (front_width - handle_w) / 2
        handle_y = drawer_y + (front_height - handle_h) / 2
        ax.add_patch(
            patches.Rectangle(
                (handle_x, handle_y),
                handle_w,
                handle_h,
                facecolor='#4B5563',
                edgecolor='#374151',
                linewidth=0.8,
                alpha=0.95
            )
        )

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
        st.session_state.saved_project_snapshot = serialize_project_state(copy.deepcopy(loaded_project))

    project = st.session_state.edit_project
    saved_snapshot = st.session_state.get('saved_project_snapshot', serialize_project_state(copy.deepcopy(project)))
    
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

    current_snapshot = serialize_project_state(copy.deepcopy(project))
    has_unsaved_changes = current_snapshot != saved_snapshot
    enable_unsaved_changes_guard(has_unsaved_changes)

    if has_unsaved_changes:
        st.warning("Hay cambios sin guardar.")

    col_back, _ = st.columns([1, 3])
    with col_back:
        if st.button("← Volver a lista"):
            if has_unsaved_changes:
                st.session_state.confirm_leave_project = True
            else:
                st.session_state.project_mode = 'list'
                st.session_state.edit_project = None
                st.session_state.edit_project_cache_id = None
                st.rerun()

    if st.session_state.get('confirm_leave_project'):
        st.warning("Tienes cambios sin guardar. ¿Quieres salir igualmente?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Salir sin guardar", key="confirm_leave_yes"):
                st.session_state.confirm_leave_project = False
                st.session_state.project_mode = 'list'
                st.session_state.edit_project = None
                st.session_state.edit_project_cache_id = None
                st.rerun()
        with c2:
            if st.button("Cancelar", key="confirm_leave_no"):
                st.session_state.confirm_leave_project = False
                st.rerun()

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
                st.session_state.saved_project_snapshot = serialize_project_state(copy.deepcopy(project))
                st.success(success_msg)
                if "creado" in success_msg:
                    st.rerun()
            except Exception as e:
                st.error(f"Error guardando proyecto: {str(e)}")
    
    with col_delete:
        if st.session_state.current_project_id:
            if st.button("🗑️ Eliminar", use_container_width=True):
                st.session_state.confirm_delete_project = True

    if st.session_state.get('confirm_delete_project') and st.session_state.current_project_id:
        st.error("¿Confirmas eliminar este proyecto?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🗑️ Sí, eliminar proyecto", key="confirm_delete_project_yes", use_container_width=True):
                try:
                    firebase.delete_project(st.session_state.current_project_id)
                    st.success("Proyecto eliminado")
                    st.session_state.confirm_delete_project = False
                    st.session_state.project_mode = 'list'
                    st.session_state.current_project_id = None
                    st.session_state.edit_project = None
                    st.session_state.edit_project_cache_id = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Error eliminando: {str(e)}")
        with c2:
            if st.button("Cancelar", key="confirm_delete_project_no", use_container_width=True):
                st.session_state.confirm_delete_project = False
                st.rerun()
    
    st.markdown("---")
    
    # Tabs para las secciones
    tabs = st.tabs(["📦 Módulos", "📏 Estantes", "🪵 Maderas", "🔩 Herrajes", "💰 Costos", "📈 Resultado", "📊 Vista Gráfica", "📄 PDF"])
    
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
                'ancho_mm': 1000,
                'alto_mm': 2000,
                'profundo_mm': 400,
                'cantidad_modulos': 1,
                'material': '',
                'material_fondo': '',
                'material_puerta': '',
                'tiene_fondo': False,
                'tiene_puertas': False,
                'cantidad_puertas': 0,
                'cantidad_estantes': 0,
                'cantidad_divisiones': 0,
                'herrajes': [],
                'cajones': get_default_drawer_config()
            })

        module_hardware_list, module_hardware_dict = get_hardware_catalog_by_category(firebase, allowed_categories={'Bisagra', 'Item general'})
        module_hardware_options_by_category = {
            'Bisagra': [h['type'] for h in module_hardware_list if h.get('category') == 'Bisagra'],
            'Item general': [h['type'] for h in module_hardware_list if h.get('category') == 'Item general']
        }
        slide_list, slide_dict = get_hardware_catalog_by_category(firebase, allowed_categories={'Corredera'})
        slide_options = [s['type'] for s in slide_list]

        for idx, module in enumerate(project.get('modules', [])):
            with st.expander(f"Módulo {idx + 1}: {module.get('nombre', '')}"):
                col1, col2 = st.columns(2)

                with col1:
                    module['nombre'] = st.text_input("Nombre", module.get('nombre', ''), key=f"mod_name_{idx}")
                    module['ancho_mm'] = st.number_input("Ancho (mm)", value=module.get('ancho_mm', 1000), key=f"mod_ancho_{idx}")
                    module['alto_mm'] = st.number_input("Alto (mm)", value=module.get('alto_mm', 2000), key=f"mod_alto_{idx}")
                    module['profundo_mm'] = st.number_input("Profundidad (mm)", value=module.get('profundo_mm', 400), key=f"mod_prof_{idx}")
                    module['cantidad_modulos'] = st.number_input(
                        "Cantidad de módulos iguales",
                        value=int(module.get('cantidad_modulos', 1)),
                        min_value=1,
                        step=1,
                        key=f"mod_cantidad_{idx}",
                        help="Multiplica piezas, superficies y herrajes de este módulo."
                    )

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
                        material_puerta = module.get('material_puerta', module.get('material', ''))
                        if material_options:
                            door_default_index = material_options.index(material_puerta) if material_puerta in material_options else 0
                            module['material_puerta'] = st.selectbox(
                                "Material puerta",
                                material_options,
                                index=door_default_index,
                                format_func=lambda x: material_labels.get(x, x),
                                key=f"mod_door_mat_{idx}"
                            )
                    else:
                        module['cantidad_puertas'] = 0
                        module['material_puerta'] = ''

                    module['cantidad_estantes'] = st.number_input("Cantidad estantes", value=module.get('cantidad_estantes', 0), min_value=0, key=f"mod_est_{idx}")
                    module['cantidad_divisiones'] = st.number_input("Cantidad divisiones", value=module.get('cantidad_divisiones', 0), min_value=0, key=f"mod_div_{idx}")

                st.markdown("**Herrajes del módulo**")
                module.setdefault('herrajes', [])

                if st.button("➕ Agregar item al módulo", key=f"mod_add_hw_{idx}"):
                    module['herrajes'].append({'type': 'Personalizado', 'category': 'Item general', 'quantity': 1, 'price_unit': 0.0})

                for hw_idx, mod_hw in enumerate(module.get('herrajes', [])):
                    hw_cols = st.columns([1.2, 2, 1, 1, 1])
                    with hw_cols[0]:
                        selected_category = st.selectbox(
                            "Categoría",
                            ["Bisagra", "Item general"],
                            index=0 if mod_hw.get('category', 'Item general') == "Bisagra" else 1,
                            key=f"mod_hw_cat_{idx}_{hw_idx}"
                        )
                        mod_hw['category'] = selected_category

                    with hw_cols[1]:
                        filtered_hardware_options = module_hardware_options_by_category.get(selected_category, [])
                        hw_type_options = ["Personalizado"] + filtered_hardware_options
                        selected_hw = st.selectbox(
                            "Tipo",
                            hw_type_options,
                            index=hw_type_options.index(mod_hw.get('type', 'Personalizado')) if mod_hw.get('type', 'Personalizado') in hw_type_options else 0,
                            key=f"mod_hw_type_{idx}_{hw_idx}"
                        )
                        if selected_hw == "Personalizado":
                            mod_hw['type'] = st.text_input("Nombre", value=mod_hw.get('type', ''), key=f"mod_hw_custom_{idx}_{hw_idx}") or "Personalizado"
                        else:
                            mod_hw['type'] = selected_hw
                            catalog_hw = module_hardware_dict.get(selected_hw, {})
                            mod_hw['price_unit'] = catalog_hw.get('price_unit', 0.0)
                            mod_hw['category'] = catalog_hw.get('category', selected_category)

                    with hw_cols[2]:
                        mod_hw['quantity'] = st.number_input("Cant.", value=int(mod_hw.get('quantity', 1)), min_value=1, key=f"mod_hw_qty_{idx}_{hw_idx}")
                    with hw_cols[3]:
                        mod_hw['price_unit'] = st.number_input(
                            "P. unitario (€)",
                            value=float(mod_hw.get('price_unit', 0.0)),
                            min_value=0.0,
                            disabled=selected_hw != "Personalizado",
                            key=f"mod_hw_price_{idx}_{hw_idx}"
                        )
                    with hw_cols[4]:
                        if st.button("🗑️", key=f"mod_hw_del_{idx}_{hw_idx}"):
                            module['herrajes'].pop(hw_idx)
                            st.rerun()

                module.setdefault('cajones', get_default_drawer_config(module.get('material', '')))
                drawers = module['cajones']
                drawers.setdefault('cantidad_cajones', 0)
                drawers.setdefault('corredera', {'type': 'Personalizado', 'category': 'Corredera', 'price_unit': 0.0})

                add_drawer_col, clear_drawer_col = st.columns([1, 1])
                with add_drawer_col:
                    if st.button("➕ Agregar cajón", key=f"mod_draw_add_{idx}", use_container_width=True):
                        drawers['enabled'] = True
                        drawers['cantidad_cajones'] = int(drawers.get('cantidad_cajones', 0)) + 1
                        if int(drawers.get('ancho_mm', 0)) <= 0:
                            drawers['ancho_mm'] = int(module.get('ancho_mm', 1000))
                        if int(drawers.get('profundo_mm', 0)) <= 0:
                            drawers['profundo_mm'] = int(module.get('profundo_mm', 400))
                with clear_drawer_col:
                    if drawers.get('enabled', False) and st.button("🗑️ Quitar cajones", key=f"mod_draw_clear_{idx}", use_container_width=True):
                        drawers['enabled'] = False
                        drawers['cantidad_cajones'] = 0

                drawers['enabled'] = int(drawers.get('cantidad_cajones', 0)) > 0

                if drawers['enabled']:
                    drawers['tipo'] = st.selectbox(
                        "Tipo de cajón",
                        ["Magic", "Completo"],
                        index=0 if drawers.get('tipo', 'Magic') == 'Magic' else 1,
                        key=f"mod_draw_type_{idx}"
                    )

                    drawer_material = drawers.get('material', module.get('material', ''))
                    if material_options:
                        default_draw_material_idx = material_options.index(drawer_material) if drawer_material in material_options else 0
                        drawers['material'] = st.selectbox(
                            "Material cajón",
                            material_options,
                            index=default_draw_material_idx,
                            format_func=lambda x: material_labels.get(x, x),
                            key=f"mod_draw_mat_{idx}"
                        )
                    else:
                        drawers['material'] = drawer_material

                    selected_slide = st.selectbox(
                        "Corredera",
                        ["Personalizado"] + slide_options,
                        index=(["Personalizado"] + slide_options).index(drawers.get('corredera', {}).get('type', 'Personalizado')) if drawers.get('corredera', {}).get('type', 'Personalizado') in (["Personalizado"] + slide_options) else 0,
                        key=f"mod_draw_slide_type_{idx}"
                    )

                    drawers['cantidad_cajones'] = st.number_input(
                        "Cantidad de cajones",
                        value=max(1, int(drawers.get('cantidad_cajones', 1))),
                        min_value=1,
                        step=1,
                        key=f"mod_draw_qty_{idx}"
                    )

                    if selected_slide == "Personalizado":
                        custom_slide_name = st.text_input(
                            "Nombre corredera",
                            value=drawers.get('corredera', {}).get('type', ''),
                            key=f"mod_draw_slide_custom_{idx}"
                        )
                        drawers['corredera'] = {
                            'type': custom_slide_name or 'Personalizado',
                            'category': 'Corredera',
                            'price_unit': float(drawers.get('corredera', {}).get('price_unit', 0.0)),
                            'quantity': int(drawers.get('cantidad_cajones', 1))
                        }
                        drawers['corredera']['price_unit'] = st.number_input(
                            "P. unitario corredera (€)",
                            value=float(drawers['corredera'].get('price_unit', 0.0)),
                            min_value=0.0,
                            key=f"mod_draw_slide_price_{idx}"
                        )
                    else:
                        drawers['corredera'] = {
                            'type': selected_slide,
                            'category': 'Corredera',
                            'price_unit': slide_dict.get(selected_slide, {}).get('price_unit', 0.0),
                            'quantity': int(drawers.get('cantidad_cajones', 1))
                        }

                    st.markdown("**Medidas del cajón**")
                    dim_col1, dim_col2, dim_col3 = st.columns(3)
                    with dim_col1:
                        drawers['alto_mm'] = st.number_input("Alto cajón (mm)", value=int(drawers.get('alto_mm', 150)), min_value=1, key=f"mod_draw_height_{idx}")
                    with dim_col2:
                        drawers['ancho_mm'] = st.number_input("Ancho cajón (mm)", value=int(drawers.get('ancho_mm', module.get('ancho_mm', 1000))), min_value=1, key=f"mod_draw_width_{idx}")
                    with dim_col3:
                        drawers['profundo_mm'] = st.number_input("Profundo cajón (mm)", value=int(drawers.get('profundo_mm', module.get('profundo_mm', 400))), min_value=1, key=f"mod_draw_depth_{idx}")
                actions_col1, actions_col2 = st.columns(2)
                with actions_col1:
                    if st.button(f"📄 Copiar módulo {idx + 1}", key=f"copy_mod_{idx}", use_container_width=True):
                        cloned_module = copy.deepcopy(module)
                        cloned_module['nombre'] = f"{module.get('nombre', f'Módulo {idx + 1}')} (copia)"
                        project['modules'].insert(idx + 1, cloned_module)
                        st.rerun()

                delete_key = f"confirm_del_mod_{idx}"
                with actions_col2:
                    if st.button(f"🗑️ Eliminar módulo {idx + 1}", key=f"del_mod_{idx}", use_container_width=True):
                        st.session_state[delete_key] = True
                    if st.session_state.get(delete_key):
                        st.warning("¿Eliminar este módulo?")
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("Confirmar", key=f"ok_del_mod_{idx}"):
                                project['modules'].pop(idx)
                                st.session_state[delete_key] = False
                                st.rerun()
                        with c2:
                            if st.button("Cancelar", key=f"cancel_del_mod_{idx}"):
                                st.session_state[delete_key] = False
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
                st.session_state.saved_project_snapshot = serialize_project_state(copy.deepcopy(project))
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
                
                delete_key = f"confirm_del_shelf_{idx}"
                if st.button(f"🗑️ Eliminar estante {idx + 1}", key=f"del_shelf_{idx}"):
                    st.session_state[delete_key] = True
                if st.session_state.get(delete_key):
                    st.warning("¿Eliminar este estante?")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Confirmar", key=f"ok_del_shelf_{idx}"):
                            project['shelves'].pop(idx)
                            st.session_state[delete_key] = False
                            st.rerun()
                    with c2:
                        if st.button("Cancelar", key=f"cancel_del_shelf_{idx}"):
                            st.session_state[delete_key] = False
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
                st.session_state.saved_project_snapshot = serialize_project_state(copy.deepcopy(project))
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
                    wood['profundo_mm'] = st.number_input("Alto (mm)", value=wood.get('profundo_mm', 200), key=f"wood_prof_{idx}")
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
                
                delete_key = f"confirm_del_wood_{idx}"
                if st.button(f"🗑️ Eliminar madera {idx + 1}", key=f"del_wood_{idx}"):
                    st.session_state[delete_key] = True
                if st.session_state.get(delete_key):
                    st.warning("¿Eliminar esta madera?")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Confirmar", key=f"ok_del_wood_{idx}"):
                            project['woods'].pop(idx)
                            st.session_state[delete_key] = False
                            st.rerun()
                    with c2:
                        if st.button("Cancelar", key=f"cancel_del_wood_{idx}"):
                            st.session_state[delete_key] = False
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
                st.session_state.saved_project_snapshot = serialize_project_state(copy.deepcopy(project))
                st.success(success_msg)
            except Exception as e:
                st.error(f"Error guardando cambios de maderas: {str(e)}")
    
    # TAB: HERRAJES
    with tabs[3]:
        st.subheader("Herrajes")
        st.caption("Aquí puedes agregar bisagras, correderas o items generales.")
        
        # Obtener herrajes de BD
        hardware_list, hardware_dict = get_hardware_catalog_by_category(firebase)
        hardware_options = ["Personalizado"] + [h['type'] for h in hardware_list]
        
        if st.button("➕ Agregar Herraje"):
            if 'hardwares' not in project:
                project['hardwares'] = []
            project['hardwares'].append({
                'type': 'Herraje',
                'category': 'Item general',
                'quantity': 1,
                'price_unit': 0.0
            })
        
        for idx, hardware in enumerate(project.get('hardwares', [])):
            with st.expander(f"Herraje {idx + 1}: {hardware.get('type', '')}"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    category = normalize_hardware_category(hardware)
                    category_index = HARDWARE_CATEGORY_OPTIONS.index(category)
                    hardware['category'] = st.selectbox(
                        "Categoría",
                        HARDWARE_CATEGORY_OPTIONS,
                        index=category_index,
                        key=f"hw_category_{idx}"
                    )

                    available_by_category = [h['type'] for h in hardware_list if h.get('category') == hardware['category']]
                    type_options = ["Personalizado"] + available_by_category

                    current_hw_type = hardware.get('type', '')
                    default_hw = current_hw_type if current_hw_type in available_by_category else "Personalizado"
                    default_index = type_options.index(default_hw) if default_hw in type_options else 0
                    selected_hw = st.selectbox("Tipo", type_options, index=default_index, key=f"hw_type_{idx}")

                    is_custom_hardware = selected_hw == "Personalizado"
                    if is_custom_hardware:
                        hardware['type'] = st.text_input("Nombre personalizado", current_hw_type, key=f"hw_custom_{idx}")
                    else:
                        hardware['type'] = selected_hw
                        hardware['price_unit'] = hardware_dict.get(selected_hw, {}).get('price_unit', 0.0)

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

                delete_key = f"confirm_del_hw_{idx}"
                if st.button(f"🗑️ Eliminar herraje {idx + 1}", key=f"del_hw_{idx}"):
                    st.session_state[delete_key] = True
                if st.session_state.get(delete_key):
                    st.warning("¿Eliminar este herraje?")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Confirmar", key=f"ok_del_hw_{idx}"):
                            project['hardwares'].pop(idx)
                            st.session_state[delete_key] = False
                            st.rerun()
                    with c2:
                        if st.button("Cancelar", key=f"cancel_del_hw_{idx}"):
                            st.session_state[delete_key] = False
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
                st.session_state.saved_project_snapshot = serialize_project_state(copy.deepcopy(project))
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

            subtotal_materials_cost = material_total + calculations['cutting_cost']
            with col3:
                st.metric("Subtotal coste materiales", f"{subtotal_materials_cost:.2f} €")

            col_hw, _ = st.columns(2)
            with col_hw:
                st.metric("Herrajes y extras", f"{calculations['hardware_total']:.2f} €")

            st.markdown("---")
            st.subheader("🧾 Resumen de Materiales")

            material_summary_rows = build_material_summary_rows(calculations, materials_db_list)
            if material_summary_rows:
                for row in material_summary_rows:
                    material_key = f"{row['Madera']}_{row['Color']}_{row['Espesor (mm)']}"
                    with st.expander(f"{row['Madera']} | {row['m² utilizados']} m² | {row['Valor (€)']:.2f} €"):
                        st.dataframe([row], use_container_width=True, hide_index=True)
                        details = build_material_origin_details(project, material_key)
                        if details:
                            st.dataframe(details, use_container_width=True, hide_index=True)
                        else:
                            st.caption("Sin detalle de origen para esta madera.")
            else:
                st.info("No hay maderas asociadas al proyecto para resumir.")

            hardware_summary_rows = build_hardware_summary_rows(project)
            st.markdown("#### Herrajes utilizados")
            if hardware_summary_rows:
                st.dataframe(hardware_summary_rows, use_container_width=True, hide_index=True)
            else:
                st.info("No hay herrajes cargados en el proyecto.")

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

            calculations_live = CalculationService.calculate_all_project_costs(
                project,
                materials_db_list,
                cutting_service
            )
            project['materiales_total'] = material_total
            project['corte_canto_total'] = calculations['cutting_cost']
            project['herrajes_total'] = calculations['hardware_total']
            st.info(f"💼 Mano de obra en PDF: {calculations_live['labor_for_invoice']:.2f} € | 🏷️ Descuento: {calculations_live.get('discount_for_invoice', 0.0):.2f} €")
            
        except Exception as e:
            st.error(f"Error calculando costos: {str(e)}")
    
    # TAB: RESULTADO
    with tabs[5]:
        st.subheader("📈 Resultado del Proyecto")
        try:
            movements = get_economy_movements_safe(firebase)
            kpis = CalculationService.calculate_project_result_kpis(project, movements)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Monto Presupuestado", f"{kpis['monto_presupuestado']:.2f} €")
            c2.metric("Gastos Reales", f"{kpis['gastos_reales']:.2f} €")
            c3.metric("Ganancia Real", f"{kpis['ganancia_real']:.2f} €")

            pct = kpis['porcentaje_real_presupuesto']
            if pct > 100:
                c4.markdown(f"<div style='padding:1rem;border-radius:10px;background:#ffe5e5;color:#b00020;text-align:center'><b>% Real del Presupuesto</b><br><span style='font-size:1.6rem'>{pct:.1f}%</span></div>", unsafe_allow_html=True)
            else:
                c4.markdown(f"<div style='padding:1rem;border-radius:10px;background:#e7f7ed;color:#146c2e;text-align:center'><b>% Real del Presupuesto</b><br><span style='font-size:1.6rem'>{pct:.1f}%</span></div>", unsafe_allow_html=True)

            st.caption("Fórmula: (Gastos reales / (Materiales + Corte y canto + Herrajes y extras)) * 100")

            st.markdown("---")
            st.markdown("### 👷 Participación de empleados")

            all_employees = sorted(
                [emp for emp in get_all_employees_safe(firebase) if (emp.get('nombre') or '').strip()],
                key=lambda x: (x.get('nombre') or '').lower()
            )

            @st.dialog("Asignar participación de empleados")
            def render_participation_dialog():
                existing_participation = project.get('employee_participation', [])
                existing_by_name = {
                    (row.get('employee_name') or '').strip(): float(row.get('percentage', 0.0) or 0.0)
                    for row in existing_participation
                    if row.get('employee_name')
                }

                st.caption("Asigna porcentaje de participación para cada empleado.")
                participation_rows = []
                cols = st.columns(2)
                for idx, emp in enumerate(all_employees):
                    employee_name = (emp.get('nombre') or '').strip()
                    default_pct = existing_by_name.get(employee_name, 0.0)
                    with cols[idx % 2]:
                        pct_value = st.number_input(
                            f"{employee_name} (%)",
                            min_value=0.0,
                            max_value=100.0,
                            value=float(default_pct),
                            step=5.0,
                            key=f"employee_pct_{project.get('id', 'new')}_{idx}"
                        )
                    participation_rows.append({'employee_name': employee_name, 'percentage': pct_value})

                if st.button("💾 Guardar participación", type="primary"):
                    payload_rows = [
                        {'employee_name': row['employee_name'], 'percentage': float(row['percentage'])}
                        for row in participation_rows
                        if float(row.get('percentage', 0.0) or 0.0) > 0
                    ]
                    project['employee_participation'] = payload_rows
                    if project.get('id'):
                        firebase.update_project(project['id'], {'employee_participation': payload_rows})
                    st.success("Participación actualizada")
                    st.rerun()

            if st.button("✏️ Configurar participación", key=f"open_participation_{project.get('id', 'new')}"):
                render_participation_dialog()

            participation_saved = project.get('employee_participation', [])
            if participation_saved:
                project_name_normalized = (project.get('name') or '').strip().lower()
                rows = []
                for row in participation_saved:
                    employee_name = (row.get('employee_name') or '').strip()
                    pct_participation = float(row.get('percentage', 0.0) or 0.0)
                    gastos_employee = 0.0
                    for mov in movements:
                        mov_project = (mov.get('project_name') or '').strip().lower()
                        if mov_project != project_name_normalized:
                            continue
                        if mov.get('tipo') != 'Egreso':
                            continue
                        if (mov.get('origen_categoria') or '').strip().lower() != 'empleado':
                            continue
                        if (mov.get('origen_nombre') or '').strip().lower() != employee_name.lower():
                            continue
                        gastos_employee += float(mov.get('monto', 0.0) or 0.0)

                    ganancia_total = kpis['ganancia_real'] * (pct_participation / 100.0)
                    ganancia_final = kpis['ganancia_real'] - gastos_employee
                    rows.append({
                        'Empleado': employee_name,
                        '% Participación': round(pct_participation, 2),
                        'Gastos': round(gastos_employee, 2),
                        'Ganancia total': round(ganancia_total, 2),
                        'Ganancia final': round(ganancia_final, 2),
                    })

                st.dataframe(rows, use_container_width=True, hide_index=True)
            else:
                st.info("No hay participación asignada todavía.")

        except Exception as e:
            st.error(f"No fue posible calcular resultado: {str(e)}")

    # TAB: VISTA GRÁFICA
    with tabs[6]:
        st.subheader("📊 Vista Gráfica")

        # Dibujar cada módulo por separado
        if project.get('modules'):
            st.markdown("### Módulos")

            for idx, module in enumerate(project['modules']):
                alto = module.get('alto_mm', 2000)
                ancho = module.get('ancho_mm', 1000)
                profundo = module.get('profundo_mm', 400)
                fig, ax = plt.subplots(figsize=(7, 4.8))

                puertas = module.get('cantidad_puertas', 0) if module.get('tiene_puertas') else 0
                dx, dy = draw_module_structure(
                    ax,
                    0,
                    0,
                    ancho,
                    alto,
                    profundo,
                    has_back=module.get('tiene_fondo', False),
                    door_count=puertas
                )
                draw_dimension_labels(ax, 0, 0, ancho, alto, profundo, dx, dy)

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

                drawer_config = module.get('cajones', {})
                drawer_qty = int(drawer_config.get('cantidad_cajones', 0)) if drawer_config.get('enabled', False) else 0
                if drawer_qty > 0:
                    draw_module_drawers(ax, 0, 0, ancho, alto, drawer_qty)

                label = module.get('nombre', f'Módulo {idx + 1}')
                ax.text(ancho / 2, alto + (profundo * 0.35) + 45, label, ha='center', va='bottom', fontsize=11, fontweight='bold', color='#0B132B')

                ax.set_xlim(-140, ancho + (profundo * 0.35) + 140)
                ax.set_ylim(-140, alto + (profundo * 0.35) + 120)
                ax.set_aspect('equal')
                ax.axis('off')

                st.pyplot(fig)
                plt.close()

        # Dibujar estantes: cantidades del mismo item apiladas, items distintos en columnas
        if project.get('shelves'):
            st.markdown("### Estantes Independientes")

            shelves_grouped = prepare_grouped_items(project['shelves'], 'Estante')
            max_prof = max([piece['profundo_mm'] for piece in shelves_grouped]) if shelves_grouped else 300
            max_qty = max([piece['cantidad'] for piece in shelves_grouped]) if shelves_grouped else 1
            fig, ax = plt.subplots(figsize=(max(8, min(16, len(shelves_grouped) * 2.4)), max(4.8, 3.8 + max_qty * 0.5)))

            x_cursor = 0
            shelf_height = 45
            stack_gap = 68

            for piece in shelves_grouped:
                ancho = piece.get('ancho_mm', 800)
                profundo = piece.get('profundo_mm', 300)
                nombre = piece.get('nombre', 'Estante')
                qty = piece.get('cantidad', 1)
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

                top_y = (qty - 1) * stack_gap + shelf_height + (profundo * 0.30)
                ax.text(x_cursor + ancho / 2, top_y + 30, nombre, ha='center', va='bottom', fontsize=8.5, fontweight='bold')
                suffix = f" (x{qty})" if qty > 1 else ''
                ax.text(x_cursor + ancho / 2, -34, f"{format_dimensions(ancho, profundo_mm=profundo)}{suffix}", ha='center', va='top', fontsize=7.5)
                x_cursor += ancho + dx + max(120, ancho * 0.14)

            ax.set_xlim(-40, x_cursor)
            ax.set_ylim(-72, (max_qty - 1) * stack_gap + shelf_height + (max_prof * 0.42) + 95)
            ax.set_aspect('equal')
            ax.axis('off')

            st.pyplot(fig)
            plt.close()

        # Dibujar maderas: cantidades del mismo item apiladas, items distintos en columnas
        if project.get('woods'):
            st.markdown("### Maderas Independientes")

            woods_grouped = prepare_grouped_items(project['woods'], 'Madera')
            max_qty = max([piece['cantidad'] for piece in woods_grouped]) if woods_grouped else 1
            fig, ax = plt.subplots(figsize=(max(8, min(16, len(woods_grouped) * 2.2)), max(4.0, 3.0 + max_qty * 0.45)))

            x_cursor = 0
            stack_gap = 58

            for piece in woods_grouped:
                ancho = piece.get('ancho_mm', 500)
                alto = piece.get('profundo_mm', 200)
                nombre = piece.get('nombre', 'Madera')
                qty = piece.get('cantidad', 1)

                for level in range(qty):
                    y_pos = level * stack_gap
                    rect = patches.Rectangle(
                        (x_cursor, y_pos),
                        ancho,
                        alto,
                        linewidth=1.2,
                        edgecolor='saddlebrown',
                        facecolor='burlywood',
                        alpha=0.75
                    )
                    ax.add_patch(rect)

                top_y = (qty - 1) * stack_gap + alto
                ax.text(x_cursor + ancho / 2, top_y + 22, nombre, ha='center', va='bottom', fontsize=8.5, fontweight='bold')
                suffix = f" (x{qty})" if qty > 1 else ''
                ax.text(x_cursor + ancho / 2, -24, f"{format_dimensions(ancho, alto_mm=alto)}{suffix}", ha='center', va='top', fontsize=7.5)
                x_cursor += ancho + max(120, ancho * 0.16)

            ax.set_xlim(-40, x_cursor)
            max_alto = max([piece.get('profundo_mm', 200) for piece in woods_grouped]) if woods_grouped else 200
            ax.set_ylim(-55, (max_qty - 1) * stack_gap + max_alto + 70)
            ax.set_aspect('equal')
            ax.axis('off')

            st.pyplot(fig)
            plt.close()

    # TAB: PDF
    with tabs[7]:
        st.subheader("📄 Generar PDF")
        
        try:
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

            logo_base64 = firebase.get_logo_base64()

            pdf_buffer = PDFService.generate_pdf(
                project,
                calculations,
                materials_dict_for_pdf,
                logo_base64
            )

            file_name = f"Presupuesto_{project_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
            st.download_button(
                label="📥 Descargar PDF",
                data=pdf_buffer.getvalue(),
                file_name=file_name,
                mime="application/pdf",
                type="primary",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Error generando PDF: {str(e)}")
