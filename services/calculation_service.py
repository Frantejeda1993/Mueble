import math
from typing import List, Dict, Tuple

class CalculationService:
    """Servicio para todos los cálculos del proyecto"""
    
    @staticmethod
    def mm_to_m2(height_mm: float, width_mm: float) -> float:
        """Convierte medidas en mm a m²"""
        return (height_mm / 1000) * (width_mm / 1000)
    
    @staticmethod
    def calculate_module_surfaces(module: Dict) -> List[Dict]:
        """
        Calcula las superficies de un módulo
        NO descuenta espesores
        """
        surfaces = []
        
        alto = module['alto_mm']
        ancho = module['ancho_mm']
        profundo = module['profundo_mm']
        tiene_fondo = module.get('tiene_fondo', False)
        tiene_puertas = module.get('tiene_puertas', False)
        cantidad_puertas = module.get('cantidad_puertas', 0)
        cantidad_estantes = module.get('cantidad_estantes', 0)
        cantidad_divisiones = module.get('cantidad_divisiones', 0)
        material = module.get('material', '')
        material_fondo = module.get('material_fondo', material)
        
        # 2 laterales: alto × profundo
        surfaces.append({
            'descripcion': f'Lateral (x2)',
            'material': material,
            'm2_unitario': CalculationService.mm_to_m2(alto, profundo),
            'm2_total': CalculationService.mm_to_m2(alto, profundo) * 2,
            'cantidad': 2
        })
        
        # 2 horizontales: ancho × profundo
        surfaces.append({
            'descripcion': f'Horizontal (x2)',
            'material': material,
            'm2_unitario': CalculationService.mm_to_m2(ancho, profundo),
            'm2_total': CalculationService.mm_to_m2(ancho, profundo) * 2,
            'cantidad': 2
        })
        
        # Fondo: ancho × alto
        if tiene_fondo:
            surfaces.append({
                'descripcion': 'Fondo',
                'material': material_fondo,
                'm2_unitario': CalculationService.mm_to_m2(ancho, alto),
                'm2_total': CalculationService.mm_to_m2(ancho, alto),
                'cantidad': 1
            })
        
        # Puertas: ancho × alto × cantidad
        if tiene_puertas and cantidad_puertas > 0:
            surfaces.append({
                'descripcion': f'Puerta (x{cantidad_puertas})',
                'material': material,
                'm2_unitario': CalculationService.mm_to_m2(ancho, alto),
                'm2_total': CalculationService.mm_to_m2(ancho, alto) * cantidad_puertas,
                'cantidad': cantidad_puertas
            })
        
        # Estantes: ancho × profundo × cantidad
        if cantidad_estantes > 0:
            surfaces.append({
                'descripcion': f'Estante (x{cantidad_estantes})',
                'material': material,
                'm2_unitario': CalculationService.mm_to_m2(ancho, profundo),
                'm2_total': CalculationService.mm_to_m2(ancho, profundo) * cantidad_estantes,
                'cantidad': cantidad_estantes
            })
        
        # Divisiones: alto × profundo × cantidad
        if cantidad_divisiones > 0:
            surfaces.append({
                'descripcion': f'División (x{cantidad_divisiones})',
                'material': material,
                'm2_unitario': CalculationService.mm_to_m2(alto, profundo),
                'm2_total': CalculationService.mm_to_m2(alto, profundo) * cantidad_divisiones,
                'cantidad': cantidad_divisiones
            })
        
        return surfaces
    
    @staticmethod
    def calculate_shelf_surface(shelf: Dict) -> Dict:
        """Calcula superficie de estante independiente"""
        ancho = shelf['ancho_mm']
        profundo = shelf['profundo_mm']
        cantidad = shelf.get('cantidad', 1)
        material = shelf.get('material', '')
        
        m2_unitario = CalculationService.mm_to_m2(ancho, profundo)
        
        return {
            'descripcion': f'Estante independiente (x{cantidad})',
            'material': material,
            'm2_unitario': m2_unitario,
            'm2_total': m2_unitario * cantidad,
            'cantidad': cantidad
        }
    
    @staticmethod
    def calculate_wood_surface(wood: Dict) -> Dict:
        """Calcula superficie de madera independiente"""
        ancho = wood['ancho_mm']
        profundo = wood['profundo_mm']
        cantidad = wood.get('cantidad', 1)
        material = wood.get('material', '')
        
        m2_unitario = CalculationService.mm_to_m2(ancho, profundo)
        
        return {
            'descripcion': f'Madera (x{cantidad})',
            'material': material,
            'm2_unitario': m2_unitario,
            'm2_total': m2_unitario * cantidad,
            'cantidad': cantidad
        }
    
    @staticmethod
    def group_surfaces_by_material(all_surfaces: List[Dict]) -> Dict[str, float]:
        """Agrupa superficies por tipo de material"""
        material_totals = {}
        
        for surface in all_surfaces:
            material = surface['material']
            m2 = surface['m2_total']
            
            if material in material_totals:
                material_totals[material] += m2
            else:
                material_totals[material] = m2
        
        return material_totals
    
    @staticmethod
    def calculate_material_cost(m2_total: float, 
                               waste_factor: float,
                               board_height_mm: float,
                               board_width_mm: float,
                               board_price: float) -> Dict:
        """
        Calcula el costo de material
        1. Aplica desperdicio
        2. Calcula tablas necesarias
        3. Calcula costo
        """
        # 1. Aplicar desperdicio
        m2_con_desperdicio = m2_total * (1 + waste_factor)
        
        # 2. Calcular superficie de una tabla
        board_m2 = CalculationService.mm_to_m2(board_height_mm, board_width_mm)
        if board_m2 <= 0:
            return {
                'm2_sin_desperdicio': m2_total,
                'm2_con_desperdicio': m2_con_desperdicio,
                'board_m2': board_m2,
                'boards_needed': 0,
                'board_price': board_price,
                'material_cost': 0.0
            }
        
        # 3. Calcular cantidad de tablas necesarias
        boards_needed = math.ceil(m2_con_desperdicio / board_m2)
        
        # 4. Calcular costo
        material_cost = boards_needed * board_price
        
        return {
            'm2_sin_desperdicio': m2_total,
            'm2_con_desperdicio': m2_con_desperdicio,
            'board_m2': board_m2,
            'boards_needed': boards_needed,
            'board_price': board_price,
            'material_cost': material_cost
        }
    
    @staticmethod
    def calculate_cutting_cost(m2_con_desperdicio: float,
                              price_per_m2: float,
                              waste_factor_cutting: float) -> float:
        """Calcula el costo del servicio de corte y canto"""
        return m2_con_desperdicio * price_per_m2 * (1 + waste_factor_cutting)
    
    @staticmethod
    def calculate_hardware_total(hardwares: List[Dict]) -> float:
        """Calcula el total de herrajes"""
        total = 0.0
        for hardware in hardwares:
            price = hardware.get('price_unit', 0.0)
            quantity = hardware.get('quantity', 0)
            total += price * quantity
        return total
    
    @staticmethod
    def calculate_project_total(material_costs: Dict[str, Dict],
                               cutting_cost: float,
                               hardware_total: float,
                               labor_cost: float,
                               extra_complexity: float) -> float:
        """Calcula el total calculado del proyecto"""
        material_total = sum(cost['material_cost'] for cost in material_costs.values())
        
        total_calculated = (
            material_total +
            cutting_cost +
            hardware_total +
            labor_cost +
            extra_complexity
        )
        
        return total_calculated
    
    @staticmethod
    def calculate_labor_for_invoice(labor_cost_project: float,
                                    extra_complexity: float,
                                    final_price: float,
                                    total_calculated: float) -> float:
        """
        Calcula la mano de obra que debe aparecer en el PDF
        mano_obra_factura = labor_cost_project + extra_complexity + (final_price - total_calculated)
        """
        return labor_cost_project + extra_complexity + (final_price - total_calculated)
    
    @staticmethod
    def calculate_all_project_costs(project_data: Dict, 
                                    materials_db: List[Dict],
                                    cutting_service: Dict) -> Dict:
        """
        Calcula todos los costos del proyecto
        Retorna un diccionario completo con todos los cálculos
        """
        # Crear diccionario de materiales por tipo-color-espesor
        materials_dict = {}
        for mat in materials_db:
            key = f"{mat['type']}_{mat.get('color', '')}_{mat.get('thickness_mm', 0)}"
            materials_dict[key] = mat
        
        # Recolectar todas las superficies
        all_surfaces = []
        
        # Procesar módulos
        for module in project_data.get('modules', []):
            surfaces = CalculationService.calculate_module_surfaces(module)
            all_surfaces.extend(surfaces)
        
        # Procesar estantes
        for shelf in project_data.get('shelves', []):
            surface = CalculationService.calculate_shelf_surface(shelf)
            all_surfaces.append(surface)
        
        # Procesar maderas
        for wood in project_data.get('woods', []):
            surface = CalculationService.calculate_wood_surface(wood)
            all_surfaces.append(surface)
        
        # Agrupar por material
        material_totals = CalculationService.group_surfaces_by_material(all_surfaces)
        
        # Calcular costos por material
        material_costs = {}
        total_m2_con_desperdicio = 0.0
        
        for material_key, m2_total in material_totals.items():
            if material_key in materials_dict:
                mat = materials_dict[material_key]
                cost_data = CalculationService.calculate_material_cost(
                    m2_total,
                    mat.get('waste_factor', 0.0),
                    mat.get('board_height_mm', 0),
                    mat.get('board_width_mm', 0),
                    mat.get('board_price', 0.0)
                )
                material_costs[material_key] = cost_data
                total_m2_con_desperdicio += cost_data['m2_con_desperdicio']
        
        # Calcular costo de corte
        cutting_cost = CalculationService.calculate_cutting_cost(
            total_m2_con_desperdicio,
            cutting_service.get('price_per_m2', 0.0),
            cutting_service.get('waste_factor', 0.0)
        )
        
        # Calcular total de herrajes
        hardware_total = CalculationService.calculate_hardware_total(
            project_data.get('hardwares', [])
        )
        
        # Calcular total del proyecto
        total_calculated = CalculationService.calculate_project_total(
            material_costs,
            cutting_cost,
            hardware_total,
            project_data.get('labor_cost_project', 0.0),
            project_data.get('extra_complexity', 0.0)
        )
        
        # Precio final (por defecto = total calculado)
        final_price = project_data.get('final_price', total_calculated)
        
        # Mano de obra para factura
        labor_for_invoice = CalculationService.calculate_labor_for_invoice(
            project_data.get('labor_cost_project', 0.0),
            project_data.get('extra_complexity', 0.0),
            final_price,
            total_calculated
        )
        
        return {
            'all_surfaces': all_surfaces,
            'material_totals': material_totals,
            'material_costs': material_costs,
            'cutting_cost': cutting_cost,
            'hardware_total': hardware_total,
            'total_calculated': total_calculated,
            'final_price': final_price,
            'labor_for_invoice': labor_for_invoice,
            'total_m2_con_desperdicio': total_m2_con_desperdicio
        }
