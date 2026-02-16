import streamlit as st
from google.cloud import firestore
from google.api_core import exceptions as gcloud_exceptions
import firebase_admin
from firebase_admin import credentials
import json
import base64
from typing import List, Dict, Optional
from datetime import datetime
import time

class FirebaseService:
    """Servicio para manejar todas las operaciones con Firebase"""
    
    def __init__(self):
        """Inicializa la conexión con Firebase"""
        self.project_id = self._init_firebase()
        try:
            # Crear cliente de Firestore con project_id explícito
            self.db = firestore.Client(project=self.project_id)
        except Exception as e:
            st.error(f"Error conectando con Firestore: {str(e)}")
            st.info("Verifica que Firestore esté activado en tu proyecto de Firebase")
            raise
    
    def _init_firebase(self) -> str:
        """Inicializa Firebase Admin SDK y retorna el project_id"""
        # Si ya está inicializado, obtener project_id
        if firebase_admin._apps:
            app = firebase_admin.get_app()
            return app.project_id
        
        try:
            # Intentar obtener credenciales de Streamlit secrets
            if 'firebase' in st.secrets:
                cred_dict = dict(st.secrets['firebase'])
                
                # Validar campos requeridos
                required_fields = ['type', 'project_id', 'private_key', 'client_email']
                missing_fields = [field for field in required_fields if field not in cred_dict]
                
                if missing_fields:
                    st.error(f"❌ Faltan campos en secrets: {', '.join(missing_fields)}")
                    st.info("Ve a Settings > Secrets en Streamlit Cloud y verifica la configuración")
                    raise ValueError(f"Missing required fields: {missing_fields}")
                
                project_id = cred_dict['project_id']
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                
                return project_id
                
            else:
                # Para desarrollo local, intentar cargar desde archivo
                try:
                    with open('firebase-credentials.json', 'r') as f:
                        cred_data = json.load(f)
                    
                    project_id = cred_data.get('project_id')
                    if not project_id:
                        raise ValueError("project_id not found in credentials")
                    
                    cred = credentials.Certificate('firebase-credentials.json')
                    firebase_admin.initialize_app(cred)
                    
                    return project_id
                    
                except FileNotFoundError:
                    st.error("❌ No se encontró configuración de Firebase")
                    st.info("""
                    **Para desarrollo local:**
                    - Descarga firebase-credentials.json de Firebase Console
                    - Guárdalo en la raíz del proyecto
                    
                    **Para Streamlit Cloud:**
                    - Ve a Settings > Secrets
                    - Configura las credenciales según secrets.example.toml
                    """)
                    raise
                    
        except Exception as e:
            if "already exists" not in str(e).lower():
                st.error(f"❌ Error inicializando Firebase: {str(e)}")
                raise
    
    # ========== PROYECTOS ==========

    def _run_with_retries(self, operation, *, max_retries: int = 3, base_delay: float = 1.5):
        """Ejecuta una operación de Firestore con reintentos en errores transitorios."""
        attempt = 0
        while True:
            try:
                return operation()
            except (gcloud_exceptions.DeadlineExceeded,
                    gcloud_exceptions.ServiceUnavailable,
                    gcloud_exceptions.InternalServerError,
                    gcloud_exceptions.RetryError) as e:
                attempt += 1
                if attempt > max_retries:
                    raise Exception(
                        "Timeout de Firebase tras varios intentos. "
                        "Revisa conexión/red y el estado de Firestore."
                    ) from e

                delay = base_delay * attempt
                time.sleep(delay)
    
    def create_project(self, project_data: Dict) -> str:
        """Crea un nuevo proyecto"""
        try:
            # Configurar timeout más largo
            doc_ref = self.db.collection('projects').document()
            project_data['date'] = datetime.now()

            # Intentar crear con timeout + reintentos en errores transitorios
            self._run_with_retries(lambda: doc_ref.set(project_data, timeout=60.0))
            return doc_ref.id
        except Exception as e:
            raise Exception(f"Error creando proyecto: {str(e)}")
    
    def get_project(self, project_id: str) -> Optional[Dict]:
        """Obtiene un proyecto por ID"""
        try:
            doc = self.db.collection('projects').document(project_id).get(timeout=15.0)
            if doc.exists:
                data = doc.to_dict()
                data['id'] = doc.id
                return data
            return None
        except Exception as e:
            raise Exception(f"Error obteniendo proyecto: {str(e)}")
    
    def get_all_projects(self) -> List[Dict]:
        """Obtiene todos los proyectos"""
        try:
            projects = []
            docs = self.db.collection('projects').stream(timeout=20.0)
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                projects.append(data)
            return projects
        except Exception as e:
            raise Exception(f"Error obteniendo proyectos: {str(e)}")
    
    def update_project(self, project_id: str, project_data: Dict):
        """Actualiza un proyecto existente"""
        try:
            self.db.collection('projects').document(project_id).update(project_data, timeout=30.0)
        except Exception as e:
            raise Exception(f"Error actualizando proyecto: {str(e)}")
    
    def delete_project(self, project_id: str):
        """Elimina un proyecto"""
        try:
            self.db.collection('projects').document(project_id).delete(timeout=15.0)
        except Exception as e:
            raise Exception(f"Error eliminando proyecto: {str(e)}")
    
    # ========== MATERIALES ==========
    
    def get_all_materials(self) -> List[Dict]:
        """Obtiene todos los materiales"""
        try:
            materials = []
            docs = self.db.collection('materials').stream(timeout=15.0)
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                materials.append(data)
            return materials
        except Exception as e:
            raise Exception(f"Error obteniendo materiales: {str(e)}")
    
    def create_material(self, material_data: Dict) -> str:
        """Crea un nuevo material"""
        try:
            doc_ref = self.db.collection('materials').document()
            doc_ref.set(material_data, timeout=15.0)
            return doc_ref.id
        except Exception as e:
            raise Exception(f"Error creando material: {str(e)}")
    
    def update_material(self, material_id: str, material_data: Dict):
        """Actualiza un material"""
        try:
            self.db.collection('materials').document(material_id).update(material_data, timeout=15.0)
        except Exception as e:
            raise Exception(f"Error actualizando material: {str(e)}")
    
    def delete_material(self, material_id: str):
        """Elimina un material"""
        try:
            self.db.collection('materials').document(material_id).delete(timeout=10.0)
        except Exception as e:
            raise Exception(f"Error eliminando material: {str(e)}")
    
    # ========== HERRAJES ==========
    
    def get_all_hardware(self) -> List[Dict]:
        """Obtiene todos los herrajes"""
        try:
            hardware = []
            docs = self.db.collection('hardware').stream(timeout=15.0)
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                hardware.append(data)
            return hardware
        except Exception as e:
            raise Exception(f"Error obteniendo herrajes: {str(e)}")
    
    def create_hardware(self, hardware_data: Dict) -> str:
        """Crea un nuevo herraje"""
        try:
            doc_ref = self.db.collection('hardware').document()
            doc_ref.set(hardware_data, timeout=15.0)
            return doc_ref.id
        except Exception as e:
            raise Exception(f"Error creando herraje: {str(e)}")
    
    def update_hardware(self, hardware_id: str, hardware_data: Dict):
        """Actualiza un herraje"""
        try:
            self.db.collection('hardware').document(hardware_id).update(hardware_data, timeout=15.0)
        except Exception as e:
            raise Exception(f"Error actualizando herraje: {str(e)}")
    
    def delete_hardware(self, hardware_id: str):
        """Elimina un herraje"""
        try:
            self.db.collection('hardware').document(hardware_id).delete(timeout=10.0)
        except Exception as e:
            raise Exception(f"Error eliminando herraje: {str(e)}")
    
    # ========== SERVICIO DE CORTE ==========
    
    def get_cutting_service(self) -> Optional[Dict]:
        """Obtiene la configuración del servicio de corte"""
        try:
            doc = self.db.collection('cutting_service').document('config').get(timeout=10.0)
            if doc.exists:
                return doc.to_dict()
            # Valores por defecto
            return {
                'price_per_m2': 0.0,
                'waste_factor': 0.10
            }
        except Exception as e:
            raise Exception(f"Error obteniendo servicio de corte: {str(e)}")
    
    def update_cutting_service(self, cutting_data: Dict):
        """Actualiza la configuración del servicio de corte"""
        try:
            self.db.collection('cutting_service').document('config').set(cutting_data, timeout=15.0)
        except Exception as e:
            raise Exception(f"Error actualizando servicio de corte: {str(e)}")
    
    # ========== LOGO (ALMACENADO EN FIRESTORE) ==========
    
    def upload_logo(self, file_bytes: bytes) -> str:
        """
        Guarda el logo en Firestore como base64
        Retorna un identificador del logo
        """
        try:
            # Convertir a base64
            logo_base64 = base64.b64encode(file_bytes).decode('utf-8')
            
            # Guardar en Firestore
            logo_data = {
                'logo_base64': logo_base64,
                'updated_at': datetime.now()
            }
            self.db.collection('config').document('logo').set(logo_data, timeout=20.0)
            
            return 'logo_stored'
        except Exception as e:
            raise Exception(f"Error guardando logo: {str(e)}")
    
    def get_logo_base64(self) -> Optional[str]:
        """Obtiene el logo en formato base64 desde Firestore"""
        try:
            doc = self.db.collection('config').document('logo').get(timeout=10.0)
            if doc.exists:
                data = doc.to_dict()
                return data.get('logo_base64')
            return None
        except Exception as e:
            return None
