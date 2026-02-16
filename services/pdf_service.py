from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from io import BytesIO
from datetime import datetime
import base64
from typing import Dict, Optional

class PDFService:
    """Servicio para generar PDFs de presupuestos"""
    
    @staticmethod
    def generate_pdf(project_data: Dict, 
                     calculations: Dict,
                     materials_db: Dict,
                     logo_base64: Optional[str] = None) -> BytesIO:
        """
        Genera un PDF del presupuesto
        
        Args:
            project_data: Datos del proyecto
            calculations: Resultados de cálculos
            materials_db: Base de datos de materiales
            logo_base64: Logo en formato base64
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                               topMargin=2*cm, bottomMargin=2*cm,
                               leftMargin=2*cm, rightMargin=2*cm)
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#34495E'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        normal_style = styles['Normal']
        
        # Contenido
        story = []
        
        # Logo (si existe)
        if logo_base64:
            try:
                # Decodificar base64 y crear imagen
                logo_bytes = base64.b64decode(logo_base64)
                logo_buffer = BytesIO(logo_bytes)
                img = Image(logo_buffer, width=4*cm, height=4*cm, kind='proportional')
                story.append(img)
                story.append(Spacer(1, 0.5*cm))
            except Exception:
                pass
        
        # Título
        story.append(Paragraph("PRESUPUESTO DE CARPINTERÍA", title_style))
        story.append(Spacer(1, 0.5*cm))
        
        # Información del proyecto
        info_data = [
            ['Proyecto:', project_data.get('name', '')],
            ['Cliente:', project_data.get('client', '')],
            ['Fecha:', project_data.get('date', datetime.now()).strftime('%d/%m/%Y') if isinstance(project_data.get('date'), datetime) else datetime.now().strftime('%d/%m/%Y')],
        ]
        
        info_table = Table(info_data, colWidths=[4*cm, 12*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ECF0F1')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2C3E50')),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 1*cm))
        
        # Desglose de materiales
        story.append(Paragraph("DESGLOSE DE MATERIALES", heading_style))
        
        material_data = [['Material', 'm² Totales', 'Tablas', 'Precio €']]
        
        for material_key, cost_data in calculations['material_costs'].items():
            # Buscar info del material
            material_info = materials_db.get(material_key, {})
            material_name = f"{material_info.get('type', material_key)} {material_info.get('color', '')} {material_info.get('thickness_mm', '')}mm"
            
            material_data.append([
                material_name,
                f"{cost_data['m2_con_desperdicio']:.2f}",
                str(cost_data['boards_needed']),
                f"{cost_data['material_cost']:.2f} €"
            ])
        
        material_table = Table(material_data, colWidths=[7*cm, 3*cm, 3*cm, 3*cm])
        material_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
        ]))
        
        story.append(material_table)
        story.append(Spacer(1, 0.5*cm))
        
        # Total materiales
        material_total = sum(cost['material_cost'] for cost in calculations['material_costs'].values())
        story.append(Paragraph(f"<b>Subtotal Materiales: {material_total:.2f} €</b>", normal_style))
        story.append(Spacer(1, 0.5*cm))
        
        # Servicio de corte
        story.append(Paragraph("SERVICIO DE CORTE Y CANTO", heading_style))
        cutting_data = [
            ['Concepto', 'Importe €'],
            ['Corte y canto', f"{calculations['cutting_cost']:.2f} €"]
        ]
        
        cutting_table = Table(cutting_data, colWidths=[10*cm, 6*cm])
        cutting_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        
        story.append(cutting_table)
        story.append(Spacer(1, 0.5*cm))
        
        # Herrajes
        if calculations['hardware_total'] > 0:
            story.append(Paragraph("HERRAJES", heading_style))
            hardware_data = [['Concepto', 'Importe €']]
            
            for hardware in project_data.get('hardwares', []):
                name = hardware.get('type', 'Herraje')
                quantity = hardware.get('quantity', 0)
                price = hardware.get('price_unit', 0.0)
                total = quantity * price
                hardware_data.append([
                    f"{name} (x{quantity})",
                    f"{total:.2f} €"
                ])
            
            hardware_table = Table(hardware_data, colWidths=[10*cm, 6*cm])
            hardware_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
            ]))
            
            story.append(hardware_table)
            story.append(Spacer(1, 0.5*cm))
            
            story.append(Paragraph(f"<b>Subtotal Herrajes: {calculations['hardware_total']:.2f} €</b>", normal_style))
            story.append(Spacer(1, 0.5*cm))
        
        # Mano de obra
        story.append(Paragraph("MANO DE OBRA", heading_style))
        labor_data = [
            ['Concepto', 'Importe €'],
            ['Mano de obra y montaje', f"{calculations['labor_for_invoice']:.2f} €"]
        ]
        
        labor_table = Table(labor_data, colWidths=[10*cm, 6*cm])
        labor_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        
        story.append(labor_table)
        story.append(Spacer(1, 1*cm))
        
        # TOTAL FINAL
        total_data = [
            ['PRECIO FINAL', f"{calculations['final_price']:.2f} €"]
        ]
        
        total_table = Table(total_data, colWidths=[10*cm, 6*cm])
        total_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#27AE60')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        story.append(total_table)
        
        # Construir PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
