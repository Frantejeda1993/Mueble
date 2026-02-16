from datetime import datetime
from typing import List, Dict, Optional

class Project:
    """Modelo de datos para un proyecto de carpintería"""
    
    def __init__(self,
                 name: str = "",
                 client: str = "",
                 date: datetime = None,
                 status: str = "Activo",
                 modules: List[Dict] = None,
                 shelves: List[Dict] = None,
                 woods: List[Dict] = None,
                 hardwares: List[Dict] = None,
                 labor_cost_project: float = 0.0,
                 extra_complexity: float = 0.0,
                 final_price: Optional[float] = None,
                 project_id: Optional[str] = None):
        
        self.id = project_id
        self.name = name
        self.client = client
        self.date = date or datetime.now()
        self.status = status
        self.modules = modules or []
        self.shelves = shelves or []
        self.woods = woods or []
        self.hardwares = hardwares or []
        self.labor_cost_project = labor_cost_project
        self.extra_complexity = extra_complexity
        self.final_price = final_price
        self.totals = {}
    
    def to_dict(self) -> Dict:
        """Convierte el proyecto a diccionario para Firebase"""
        data = {
            'name': self.name,
            'client': self.client,
            'date': self.date,
            'status': self.status,
            'modules': self.modules,
            'shelves': self.shelves,
            'woods': self.woods,
            'hardwares': self.hardwares,
            'labor_cost_project': self.labor_cost_project,
            'extra_complexity': self.extra_complexity,
            'totals': self.totals
        }
        
        if self.final_price is not None:
            data['final_price'] = self.final_price
            
        return data
    
    @staticmethod
    def from_dict(data: Dict, project_id: str = None) -> 'Project':
        """Crea un proyecto desde un diccionario de Firebase"""
        return Project(
            name=data.get('name', ''),
            client=data.get('client', ''),
            date=data.get('date'),
            status=data.get('status', 'Activo'),
            modules=data.get('modules', []),
            shelves=data.get('shelves', []),
            woods=data.get('woods', []),
            hardwares=data.get('hardwares', []),
            labor_cost_project=data.get('labor_cost_project', 0.0),
            extra_complexity=data.get('extra_complexity', 0.0),
            final_price=data.get('final_price'),
            project_id=project_id
        )
