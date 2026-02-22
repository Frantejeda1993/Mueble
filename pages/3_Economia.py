from datetime import date, datetime
import uuid

import pandas as pd
import streamlit as st

from services.calculation_service import CalculationService
from services.firebase_service import FirebaseService


def get_firebase():
    if 'firebase' not in st.session_state:
        with st.spinner("Conectando con Firebase..."):
            st.session_state.firebase = FirebaseService()
    return st.session_state.firebase


firebase = get_firebase()
st.session_state.active_nav_page = 'economy'
st.title("💹 Economía")

projects = firebase.get_all_projects()
employees = firebase.get_all_employees()
movements = firebase.get_economy_movements()

balances = CalculationService.compute_economy_balances(movements)
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Balance Taller", f"{balances['balance_taller']:.2f} €", help="Ingresos - egresos totales (incluye pendientes)")
with col2:
    st.metric("Balance Empleados Permanentes", f"{balances['balance_empleados_permanentes']:.2f} €", help="Solo origen empleado permanente, sin pendientes")
with col3:
    st.metric("Fondos Reales", f"{balances['fondos_reales']:.2f} €", help="Ingresos - egresos sin pendientes")

st.markdown("---")
st.subheader("➕ Agregar nuevo movimiento")

clients = sorted({(p.get('client') or '').strip() for p in projects if (p.get('client') or '').strip()})
project_by_client = {}
for project in projects:
    client = (project.get('client') or '').strip()
    if not client:
        continue
    project_by_client.setdefault(client, []).append(project)

for client_name in project_by_client:
    project_by_client[client_name] = sorted(
        project_by_client[client_name],
        key=lambda x: x.get('date') or datetime.min,
        reverse=True,
    )

with st.form("economy_new_movement"):
    fecha = st.date_input("Fecha", value=date.today())
    origen_categoria = st.selectbox("Origen", ["Cliente", "Empleado", "Inversión", "Mantenimiento"])

    selected_client = None
    selected_employee = None
    split_distribution = []

    if origen_categoria == "Cliente":
        selected_client = st.selectbox("Cliente", options=clients) if clients else None
        client_projects = project_by_client.get(selected_client, []) if selected_client else []

        if len(client_projects) > 1:
            st.caption("Cliente con múltiples proyectos activos. Puedes ajustar la distribución por porcentaje.")
            remaining = 100
            for idx, project in enumerate(client_projects):
                default = 100 if idx == 0 else 0
                percent = st.number_input(
                    f"% para {project.get('name', f'Proyecto {idx+1}')}",
                    min_value=0,
                    max_value=100,
                    value=default,
                    key=f"split_{project.get('id', idx)}"
                )
                remaining -= percent
                split_distribution.append({'project_id': project.get('id'), 'project_name': project.get('name'), 'percent': percent})
            st.caption(f"Total asignado: {100-remaining}%")
        elif len(client_projects) == 1:
            split_distribution.append({'project_id': client_projects[0].get('id'), 'project_name': client_projects[0].get('name'), 'percent': 100})

    if origen_categoria == "Empleado":
        employee_names = [emp.get('nombre') for emp in employees]
        selected_employee = st.selectbox("Empleado", options=employee_names) if employee_names else None

    tipo = st.selectbox("Tipo", ["Ingreso", "Egreso", "Pendiente de pago"])
    referencia = st.text_input("Referencia")
    descripcion = st.text_area("Descripción")
    monto = st.number_input("Monto", min_value=0.0, value=0.0, step=10.0)

    submitted = st.form_submit_button("Guardar movimiento", type="primary")
    if submitted:
        if monto <= 0:
            st.error("El monto debe ser mayor a 0.")
        else:
            split_rows = CalculationService.split_amount_by_percentages(monto, split_distribution) if split_distribution else []
            created_count = 0
            batch_group_id = str(uuid.uuid4())
            if split_rows:
                for split in split_rows:
                    movement = {
                        'fecha': datetime.combine(fecha, datetime.min.time()),
                        'tipo': tipo,
                        'referencia': referencia,
                        'descripcion': descripcion,
                        'monto': split.get('amount', 0.0),
                        'origen_categoria': origen_categoria,
                        'origen_nombre': selected_client,
                        'project_id': split.get('project_id'),
                        'project_name': split.get('project_name'),
                        'split_percent': split.get('percent'),
                        'split_group_id': batch_group_id,
                    }
                    movement_id = firebase.create_economy_movement(movement)
                    firebase.log_economy_action('crear', movement_id)
                    created_count += 1
            else:
                employee_type = None
                if origen_categoria == 'Empleado' and selected_employee:
                    employee_type = next((emp.get('tipo_puesto') for emp in employees if emp.get('nombre') == selected_employee), None)

                movement = {
                    'fecha': datetime.combine(fecha, datetime.min.time()),
                    'tipo': tipo,
                    'referencia': referencia,
                    'descripcion': descripcion,
                    'monto': monto,
                    'origen_categoria': origen_categoria,
                    'origen_nombre': selected_employee if origen_categoria == 'Empleado' else origen_categoria,
                    'empleado_tipo': employee_type,
                    'split_group_id': batch_group_id,
                }
                movement_id = firebase.create_economy_movement(movement)
                firebase.log_economy_action('crear', movement_id)
                created_count = 1

            st.success(f"Movimientos creados: {created_count}")
            st.rerun()

st.markdown("---")
st.subheader("📋 Lista de movimientos")

filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
with filter_col1:
    filter_date = st.date_input("Filtrar por fecha", value=None)
with filter_col2:
    filter_project = st.selectbox("Proyecto", ["Todos"] + sorted({m.get('project_name') for m in movements if m.get('project_name')}))
with filter_col3:
    filter_client = st.selectbox("Cliente", ["Todos"] + sorted({m.get('origen_nombre') for m in movements if m.get('origen_categoria') == 'Cliente'}))
with filter_col4:
    filter_type = st.selectbox("Tipo", ["Todos", "Ingreso", "Egreso", "Pendiente de pago"])

filtered = []
for mov in movements:
    mov_date = mov.get('fecha')
    mov_date_only = mov_date.date() if hasattr(mov_date, 'date') else None
    if filter_date and mov_date_only != filter_date:
        continue
    if filter_project != 'Todos' and mov.get('project_name') != filter_project:
        continue
    if filter_client != 'Todos' and mov.get('origen_nombre') != filter_client:
        continue
    if filter_type != 'Todos' and mov.get('tipo') != filter_type:
        continue
    filtered.append(mov)

filtered = sorted(filtered, key=lambda x: x.get('fecha') or datetime.min, reverse=True)

for mov in filtered:
    row = st.columns([1.2, 1.3, 1, 1.2, 2.2, 2])
    badge_color = {'Ingreso': '🟢', 'Egreso': '🔴', 'Pendiente de pago': '🟡'}.get(mov.get('tipo'), '⚪')
    row[0].write((mov.get('fecha').strftime('%d/%m/%Y') if mov.get('fecha') else '-'))
    row[1].write(mov.get('referencia', '-'))
    row[2].write(f"{badge_color} {mov.get('tipo', '-')}")
    row[3].write(mov.get('origen_nombre', '-'))
    row[4].write(mov.get('descripcion', '-'))

    with row[5]:
        c1, c2, c3 = st.columns(3)
        if c1.button("✏️", key=f"edit_{mov['id']}"):
            st.session_state[f"editing_{mov['id']}"] = True
        if c2.button("📄", key=f"dup_{mov['id']}"):
            duplicate = {k: v for k, v in mov.items() if k not in ('id', 'created_at', 'updated_at')}
            duplicate_id = firebase.create_economy_movement(duplicate)
            firebase.log_economy_action('crear', duplicate_id)
            st.success("Movimiento duplicado")
            st.rerun()
        if c3.button("🗑️", key=f"del_{mov['id']}"):
            st.session_state[f"confirm_del_{mov['id']}"] = True

    if st.session_state.get(f"confirm_del_{mov['id']}"):
        st.warning("¿Confirmas eliminar este movimiento?")
        cc1, cc2 = st.columns(2)
        if cc1.button("Confirmar", key=f"ok_del_{mov['id']}"):
            firebase.log_economy_action('eliminar', mov['id'], snapshot_before=mov)
            firebase.delete_economy_movement(mov['id'])
            st.session_state[f"confirm_del_{mov['id']}"] = False
            st.rerun()
        if cc2.button("Cancelar", key=f"cancel_del_{mov['id']}"):
            st.session_state[f"confirm_del_{mov['id']}"] = False
            st.rerun()

    if st.session_state.get(f"editing_{mov['id']}"):
        with st.form(f"form_edit_{mov['id']}"):
            new_ref = st.text_input("Referencia", value=mov.get('referencia', ''))
            new_desc = st.text_input("Descripción", value=mov.get('descripcion', ''))
            new_monto = st.number_input("Monto", min_value=0.0, value=float(mov.get('monto', 0.0) or 0.0), key=f"monto_{mov['id']}")
            submit_edit = st.form_submit_button("Guardar cambios")
            if submit_edit:
                before = dict(mov)
                mov['referencia'] = new_ref
                mov['descripcion'] = new_desc
                mov['monto'] = new_monto
                firebase.update_economy_movement(mov['id'], mov)
                firebase.log_economy_action('editar', mov['id'], snapshot_before=before)
                st.session_state[f"editing_{mov['id']}"] = False
                st.success("Movimiento actualizado")
                st.rerun()

if not filtered:
    st.info("No hay movimientos con los filtros seleccionados.")

if movements:
    df = pd.DataFrame(filtered)
    st.caption(f"Movimientos mostrados: {len(df)}")
