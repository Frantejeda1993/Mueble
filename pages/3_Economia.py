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


def get_all_employees_safe(firebase):
    if hasattr(firebase, 'get_all_employees'):
        return firebase.get_all_employees()

    employees = []
    docs = firebase.db.collection('referencias').document('empleados').collection('items').stream(timeout=15.0)
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        employees.append(data)
    return employees


def get_economy_movements_safe(firebase):
    if hasattr(firebase, 'get_economy_movements'):
        return firebase.get_economy_movements()

    rows = []
    docs = firebase.db.collection('economia_movimientos').stream(timeout=20.0)
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        rows.append(data)
    return sorted(rows, key=lambda x: x.get('fecha') or datetime.min, reverse=True)


def create_economy_movement_safe(firebase, movement):
    if hasattr(firebase, 'create_economy_movement'):
        return firebase.create_economy_movement(movement)
    doc_ref = firebase.db.collection('economia_movimientos').document()
    doc_ref.set({**movement, 'created_at': datetime.now()}, timeout=20.0)
    return doc_ref.id


def update_economy_movement_safe(firebase, movement_id, movement):
    if hasattr(firebase, 'update_economy_movement'):
        firebase.update_economy_movement(movement_id, movement)
        return
    firebase.db.collection('economia_movimientos').document(movement_id).update({**movement, 'updated_at': datetime.now()}, timeout=20.0)


def delete_economy_movement_safe(firebase, movement_id):
    if hasattr(firebase, 'delete_economy_movement'):
        firebase.delete_economy_movement(movement_id)
        return
    firebase.db.collection('economia_movimientos').document(movement_id).delete(timeout=15.0)


def log_economy_action_safe(firebase, action, movement_id, snapshot_before=None):
    if hasattr(firebase, 'log_economy_action'):
        firebase.log_economy_action(action, movement_id, snapshot_before=snapshot_before)
        return
    payload = {
        'timestamp': datetime.now(),
        'usuario': None,
        'accion': action,
        'movimiento_id': movement_id,
        'snapshot_previo': snapshot_before,
    }
    firebase.db.collection('economia_logs').document().set(payload, timeout=15.0)


firebase = get_firebase()
st.session_state.active_nav_page = 'economy'
st.title("💹 Economía")

projects = firebase.get_all_projects()
employees = get_all_employees_safe(firebase)
movements = get_economy_movements_safe(firebase)

balances = CalculationService.compute_economy_balances(movements)
col1, col2, col3 = st.columns(3)
col1.metric("Balance Taller", f"{balances['balance_taller']:.2f} €")
col2.metric("Balance Empleados Permanentes", f"{balances['balance_empleados_permanentes']:.2f} €")
col3.metric("Fondos Reales", f"{balances['fondos_reales']:.2f} €")

st.markdown("---")
st.subheader("➕ Movimientos")

clients = sorted({(p.get('client') or '').strip() for p in projects if (p.get('client') or '').strip()})
project_by_client = {}
for project in projects:
    client = (project.get('client') or '').strip()
    if client and project.get('status') == 'Activo':
        project_by_client.setdefault(client, []).append(project)

for client_name in project_by_client:
    project_by_client[client_name] = sorted(project_by_client[client_name], key=lambda x: x.get('date') or datetime.min)

active_projects = sorted(
    [p for p in projects if p.get('status') == 'Activo'],
    key=lambda x: (x.get('date') or datetime.min)
)
permanent_employees = sorted(
    [emp for emp in employees if (emp.get('tipo_puesto') or '').strip().lower() == 'permanente'],
    key=lambda x: (x.get('nombre') or '').lower()
)


@st.dialog("Agregar nuevo movimiento")
def render_new_movement_dialog():
    fecha = st.date_input("Fecha", value=date.today())
    origen_categoria = st.selectbox("Origen", ["Cliente", "Empleado", "Inversión", "Mantenimiento"])

        tipo = st.selectbox("Tipo", ["Ingreso", "Egreso", "Pendiente de pago"])
        referencia = st.text_input("Referencia")
        monto = st.number_input("Monto", min_value=0.0, value=0.0, step=10.0)

        if st.form_submit_button("Guardar movimiento", type="primary"):
            if monto <= 0:
                st.error("El monto debe ser mayor a 0.")
                return

    if origen_categoria == "Cliente":
        selected_client = st.selectbox("Cliente", options=clients) if clients else None
        client_projects = project_by_client.get(selected_client, []) if selected_client else []
        for idx, project in enumerate(client_projects):
            default = 100 if idx == len(client_projects) - 1 else 0
            percent = st.number_input(
                f"% para {project.get('name', f'Proyecto {idx+1}')}",
                min_value=0,
                max_value=100,
                value=default,
                key=f"split_client_{project.get('id', idx)}"
            )
            split_distribution.append({'project_id': project.get('id'), 'project_name': project.get('name'), 'percent': percent})

    if origen_categoria == "Empleado":
        employee_names = [emp.get('nombre') for emp in permanent_employees if emp.get('nombre')]
        selected_employee = st.selectbox("Empleado", options=employee_names) if employee_names else None
        for idx, project in enumerate(active_projects):
            percent = st.number_input(
                f"% para {project.get('name', f'Proyecto {idx+1}')}",
                min_value=0,
                max_value=100,
                value=0,
                key=f"split_employee_{project.get('id', idx)}"
            )
            split_distribution.append({'project_id': project.get('id'), 'project_name': project.get('name'), 'percent': percent})

    tipo = st.selectbox("Tipo", ["Ingreso", "Egreso", "Pendiente de pago"])
    referencia = st.text_input("Referencia")
    monto = st.number_input("Monto", min_value=0.0, value=0.0, step=10.0)

    if st.button("Guardar movimiento", type="primary"):
        if monto <= 0:
            st.error("El monto debe ser mayor a 0.")
            return

        split_rows = CalculationService.split_amount_by_percentages(monto, split_distribution) if split_distribution else []
        batch_group_id = str(uuid.uuid4())
        created_count = 0
        if split_rows:
            for split in split_rows:
                if float(split.get('percent', 0.0) or 0.0) <= 0:
                    continue
                movement = {
                    'fecha': datetime.combine(fecha, datetime.min.time()), 'tipo': tipo, 'referencia': referencia,
                    'monto': split.get('amount', 0.0), 'origen_categoria': origen_categoria,
                    'origen_nombre': selected_client if origen_categoria == 'Cliente' else selected_employee,
                    'project_id': split.get('project_id'), 'project_name': split.get('project_name'),
                    'split_percent': split.get('percent'), 'split_group_id': batch_group_id,
                }
                movement_id = create_economy_movement_safe(firebase, movement)
                log_economy_action_safe(firebase, 'crear', movement_id)
                created_count += 1
        else:
            employee_type = None
            if origen_categoria == 'Empleado' and selected_employee:
                employee_type = next((emp.get('tipo_puesto') for emp in employees if emp.get('nombre') == selected_employee), None)
            movement = {
                'fecha': datetime.combine(fecha, datetime.min.time()), 'tipo': tipo, 'referencia': referencia,
                'monto': monto, 'origen_categoria': origen_categoria,
                'origen_nombre': selected_employee if origen_categoria == 'Empleado' else origen_categoria,
                'empleado_tipo': employee_type, 'split_group_id': batch_group_id,
            }
            movement_id = create_economy_movement_safe(firebase, movement)
            log_economy_action_safe(firebase, 'crear', movement_id)
            created_count = 1
        st.success(f"Movimientos creados: {created_count}")
        st.rerun()


if st.button("➕ Agregar nuevo movimiento", type="primary"):
    render_new_movement_dialog()

st.markdown("---")
st.subheader("📋 Lista de movimientos")

col1, col2, col3, col4 = st.columns(4)
with col1:
    use_date_filter = st.checkbox("Filtrar por fecha")
    filter_date = st.date_input("Fecha", value=date.today(), key="economy_filter_date") if use_date_filter else None
with col2:
    filter_project = st.selectbox("Proyecto", ["Todos"] + sorted({m.get('project_name') for m in movements if m.get('project_name')}))
with col3:
    filter_client = st.selectbox("Cliente", ["Todos"] + sorted({m.get('origen_nombre') for m in movements if m.get('origen_categoria') == 'Cliente'}))
with col4:
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
    row = st.columns([1.2, 1.6, 1, 1.8, 1.8])
    badge = {'Ingreso': '🟢', 'Egreso': '🔴', 'Pendiente de pago': '🟡'}.get(mov.get('tipo'), '⚪')
    row[0].write(mov.get('fecha').strftime('%d/%m/%Y') if mov.get('fecha') else '-')
    row[1].write(mov.get('referencia', '-'))
    row[2].write(f"{badge} {mov.get('tipo', '-')}")
    row[3].write(mov.get('origen_nombre', '-'))
    with row[4]:
        a, b, c = st.columns(3)
        if a.button("✏️", key=f"edit_{mov['id']}"):
            st.session_state[f"editing_{mov['id']}"] = True
        if b.button("📄", key=f"dup_{mov['id']}"):
            duplicate = {k: v for k, v in mov.items() if k not in ('id', 'created_at', 'updated_at')}
            duplicate_id = create_economy_movement_safe(firebase, duplicate)
            log_economy_action_safe(firebase, 'crear', duplicate_id)
            st.rerun()
        if c.button("🗑️", key=f"del_{mov['id']}"):
            st.session_state[f"confirm_del_{mov['id']}"] = True

    if st.session_state.get(f"confirm_del_{mov['id']}"):
        st.warning("¿Confirmas eliminar este movimiento?")
        c1, c2 = st.columns(2)
        if c1.button("Confirmar", key=f"ok_del_{mov['id']}"):
            log_economy_action_safe(firebase, 'eliminar', mov['id'], snapshot_before=mov)
            delete_economy_movement_safe(firebase, mov['id'])
            st.session_state[f"confirm_del_{mov['id']}"] = False
            st.rerun()
        if c2.button("Cancelar", key=f"cancel_del_{mov['id']}"):
            st.session_state[f"confirm_del_{mov['id']}"] = False
            st.rerun()

    if st.session_state.get(f"editing_{mov['id']}"):
        with st.form(f"form_edit_{mov['id']}"):
            new_ref = st.text_input("Referencia", value=mov.get('referencia', ''))
            new_monto = st.number_input("Monto", min_value=0.0, value=float(mov.get('monto', 0.0) or 0.0), key=f"monto_{mov['id']}")
            if st.form_submit_button("Guardar cambios"):
                before = dict(mov)
                mov['referencia'] = new_ref
                mov['monto'] = new_monto
                update_economy_movement_safe(firebase, mov['id'], mov)
                log_economy_action_safe(firebase, 'editar', mov['id'], snapshot_before=before)
                st.session_state[f"editing_{mov['id']}"] = False
                st.rerun()

if not filtered:
    st.info("No hay movimientos con los filtros seleccionados.")
if movements:
    st.caption(f"Movimientos mostrados: {len(pd.DataFrame(filtered))}")
