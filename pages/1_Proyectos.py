import streamlit as st
from services.firebase_service import FirebaseService
from services.calculation_service import CalculationService
from services.pdf_service import PDFService
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Inicializar Firebase
@st.cache_resource
def get_firebase():
    return FirebaseService()

firebase = get_firebase()

st.title("📁 Gestión de Proyectos")

# Modo de vista
if 'project_mode' not in st.session_state:
    st.session_state.project_mode = 'list'  # 'list' o 'edit'

if 'current_project_id' not in st.session_state:
    st.session_state.current_project_id = None

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
                            st.rerun()
                    
                    st.divider()
    
    except Exception as e:
        st.error(f"Error cargando proyectos: {str(e)}")

# ========== VISTA EDICIÓN ==========
elif st.session_state.project_mode == 'edit':
    
    # Botón volver
    if st.button("← Volver a lista"):
        st.session_state.project_mode = 'list'
        st.session_state.current_project_id = None
        st.rerun()
    
    st.markdown("---")
    
    # Cargar proyecto si existe
    if st.session_state.current_project_id:
        try:
            project = firebase.get_project(st.session_state.current_project_id)
            if not project:
                st.error("Proyecto no encontrado")
                st.stop()
        except Exception as e:
            st.error(f"Error cargando proyecto: {str(e)}")
            st.stop()
    else:
        # Nuevo proyecto
        project = {
            'name': '',
            'client': '',
            'date': datetime.now(),
            'status': 'Activo',
            'modules': [],
            'shelves': [],
            'woods': [],
            'hardwares': [],
            'labor_cost_project': 0.0,
            'extra_complexity': 0.0
        }
    
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
    
    # Botón guardar
    col_save, col_delete = st.columns([3, 1])
    with col_save:
        if st.button("💾 Guardar Proyecto", type="primary", use_container_width=True):
            try:
                project_data = {
                    'name': project_name,
                    'client': project_client,
                    'date': datetime.combine(project_date, datetime.min.time()),
                    'status': project_status,
                    'modules': project.get('modules', []),
                    'shelves': project.get('shelves', []),
                    'woods': project.get('woods', []),
                    'hardwares': project.get('hardwares', []),
                    'labor_cost_project': project.get('labor_cost_project', 0.0),
                    'extra_complexity': project.get('extra_complexity', 0.0)
                }
                
                if st.session_state.current_project_id:
                    firebase.update_project(st.session_state.current_project_id, project_data)
                    st.success("✅ Proyecto actualizado correctamente")
                else:
                    new_id = firebase.create_project(project_data)
                    st.session_state.current_project_id = new_id
                    st.success("✅ Proyecto creado correctamente")
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
            material_options = [f"{m['type']} {m.get('color', '')} {m.get('thickness_mm', '')}mm" for m in materials_list]
            materials_dict = {f"{m['type']}_{m.get('color', '')}_{m.get('thickness_mm', 0)}": m for m in materials_list}
        except:
            material_options = []
            materials_dict = {}
        
        if st.button("➕ Agregar Módulo"):
            if 'modules' not in project:
                project['modules'] = []
            project['modules'].append({
                'nombre': f'Módulo {len(project["modules"]) + 1}',
                'alto_mm': 2000,
                'ancho_mm': 1000,
                'profundo_mm': 400,
                'material': '',
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
                    if material_options:
                        selected_mat = st.selectbox("Material", material_options, key=f"mod_mat_{idx}")
                        module['material'] = selected_mat.replace(' ', '_').replace('mm', '')
                    
                    module['tiene_fondo'] = st.checkbox("Tiene fondo", module.get('tiene_fondo', False), key=f"mod_fondo_{idx}")
                    module['tiene_puertas'] = st.checkbox("Tiene puertas", module.get('tiene_puertas', False), key=f"mod_puertas_{idx}")
                    
                    if module['tiene_puertas']:
                        module['cantidad_puertas'] = st.number_input("Cantidad puertas", value=module.get('cantidad_puertas', 1), min_value=0, key=f"mod_cant_puertas_{idx}")
                    
                    module['cantidad_estantes'] = st.number_input("Cantidad estantes", value=module.get('cantidad_estantes', 0), min_value=0, key=f"mod_est_{idx}")
                    module['cantidad_divisiones'] = st.number_input("Cantidad divisiones", value=module.get('cantidad_divisiones', 0), min_value=0, key=f"mod_div_{idx}")
                
                if st.button(f"🗑️ Eliminar módulo {idx + 1}", key=f"del_mod_{idx}"):
                    project['modules'].pop(idx)
                    st.rerun()
    
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
                    selected_mat = st.selectbox("Material", material_options, key=f"shelf_mat_{idx}")
                    shelf['material'] = selected_mat.replace(' ', '_').replace('mm', '')
                
                if st.button(f"🗑️ Eliminar estante {idx + 1}", key=f"del_shelf_{idx}"):
                    project['shelves'].pop(idx)
                    st.rerun()
    
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
                    selected_mat = st.selectbox("Material", material_options, key=f"wood_mat_{idx}")
                    wood['material'] = selected_mat.replace(' ', '_').replace('mm', '')
                
                if st.button(f"🗑️ Eliminar madera {idx + 1}", key=f"del_wood_{idx}"):
                    project['woods'].pop(idx)
                    st.rerun()
    
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
                    selected_hw = st.selectbox("Tipo", hardware_options, key=f"hw_type_{idx}")
                    
                    if selected_hw == "Personalizado":
                        hardware['type'] = st.text_input("Nombre personalizado", hardware.get('type', ''), key=f"hw_custom_{idx}")
                    else:
                        hardware['type'] = selected_hw
                        if selected_hw in hardware_dict:
                            hardware['price_unit'] = hardware_dict[selected_hw].get('price_unit', 0.0)
                
                with col2:
                    hardware['quantity'] = st.number_input("Cantidad", value=hardware.get('quantity', 1), min_value=0, key=f"hw_qty_{idx}")
                
                with col3:
                    hardware['price_unit'] = st.number_input("Precio unitario (€)", value=hardware.get('price_unit', 0.0), key=f"hw_price_{idx}")
                
                if st.button(f"🗑️ Eliminar herraje {idx + 1}", key=f"del_hw_{idx}"):
                    project['hardwares'].pop(idx)
                    st.rerun()
    
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
        
        # Dibujar módulos
        if project.get('modules'):
            st.markdown("### Módulos")
            
            for idx, module in enumerate(project['modules']):
                st.markdown(f"**{module.get('nombre', f'Módulo {idx+1}')}**")
                
                fig, ax = plt.subplots(figsize=(8, 6))
                
                alto = module.get('alto_mm', 2000)
                ancho = module.get('ancho_mm', 1000)
                profundo = module.get('profundo_mm', 400)
                
                # Dibujar rectángulo frontal
                rect = patches.Rectangle((0, 0), ancho, alto, linewidth=2, edgecolor='black', facecolor='lightblue', alpha=0.5)
                ax.add_patch(rect)
                
                # Indicar si tiene fondo
                if module.get('tiene_fondo'):
                    ax.text(ancho/2, alto/2, 'CON FONDO', ha='center', va='center', fontsize=12, weight='bold')
                
                # Dibujar estantes
                num_estantes = module.get('cantidad_estantes', 0)
                if num_estantes > 0:
                    spacing = alto / (num_estantes + 1)
                    for i in range(1, num_estantes + 1):
                        y_pos = i * spacing
                        ax.plot([0, ancho], [y_pos, y_pos], 'r--', linewidth=1.5)
                
                # Dibujar divisiones
                num_divisiones = module.get('cantidad_divisiones', 0)
                if num_divisiones > 0:
                    spacing = ancho / (num_divisiones + 1)
                    for i in range(1, num_divisiones + 1):
                        x_pos = i * spacing
                        ax.plot([x_pos, x_pos], [0, alto], 'g--', linewidth=1.5)
                
                # Indicar puertas
                if module.get('tiene_puertas'):
                    num_puertas = module.get('cantidad_puertas', 1)
                    ax.text(ancho/2, -alto*0.1, f'🚪 {num_puertas} puerta(s)', ha='center', fontsize=10)
                
                # Anotaciones de medidas
                ax.text(ancho/2, -alto*0.05, f'{ancho} mm', ha='center', fontsize=10)
                ax.text(-ancho*0.1, alto/2, f'{alto} mm', ha='right', va='center', rotation=90, fontsize=10)
                ax.text(ancho + ancho*0.05, alto/2, f'Prof: {profundo} mm', ha='left', va='center', fontsize=9)
                
                ax.set_xlim(-ancho*0.2, ancho*1.2)
                ax.set_ylim(-alto*0.2, alto*1.1)
                ax.set_aspect('equal')
                ax.axis('off')
                
                st.pyplot(fig)
                plt.close()
        
        # Dibujar estantes
        if project.get('shelves'):
            st.markdown("### Estantes Independientes")
            
            fig, ax = plt.subplots(figsize=(8, 4))
            
            y_offset = 0
            for idx, shelf in enumerate(project['shelves']):
                ancho = shelf.get('ancho_mm', 800)
                profundo = shelf.get('profundo_mm', 300)
                cantidad = shelf.get('cantidad', 1)
                
                for i in range(cantidad):
                    rect = patches.Rectangle((0, y_offset), ancho, 50, linewidth=1, 
                                            edgecolor='brown', facecolor='wheat', alpha=0.7)
                    ax.add_patch(rect)
                    ax.text(ancho/2, y_offset + 25, f'{ancho}x{profundo}mm', 
                           ha='center', va='center', fontsize=8)
                    y_offset += 70
            
            ax.set_xlim(-100, max([s.get('ancho_mm', 800) for s in project['shelves']]) + 100)
            ax.set_ylim(-50, y_offset + 50)
            ax.set_aspect('equal')
            ax.axis('off')
            
            st.pyplot(fig)
            plt.close()
        
        # Dibujar maderas
        if project.get('woods'):
            st.markdown("### Maderas Independientes")
            
            fig, ax = plt.subplots(figsize=(8, 4))
            
            y_offset = 0
            for idx, wood in enumerate(project['woods']):
                ancho = wood.get('ancho_mm', 500)
                profundo = wood.get('profundo_mm', 200)
                cantidad = wood.get('cantidad', 1)
                
                for i in range(cantidad):
                    rect = patches.Rectangle((0, y_offset), ancho, 40, linewidth=1, 
                                            edgecolor='saddlebrown', facecolor='burlywood', alpha=0.7)
                    ax.add_patch(rect)
                    ax.text(ancho/2, y_offset + 20, f'{ancho}x{profundo}mm', 
                           ha='center', va='center', fontsize=8)
                    y_offset += 60
            
            ax.set_xlim(-100, max([w.get('ancho_mm', 500) for w in project['woods']]) + 100)
            ax.set_ylim(-50, y_offset + 50)
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
                
                # Obtener logo
                logo_url = firebase.get_logo_url()
                
                # Generar PDF
                pdf_buffer = PDFService.generate_pdf(
                    project,
                    calculations,
                    materials_dict_for_pdf,
                    logo_url
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
