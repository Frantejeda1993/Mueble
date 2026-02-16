from reportlab.lib.pagesizes import A4
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
    def _create_table(data, col_widths, header_bg='#1F3A5F', alt_rows=True):
        table = Table(data, colWidths=col_widths)
        style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(header_bg)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8.5),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#D0D7DE')),
        ]
        if alt_rows and len(data) > 2:
            style.append(('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]))
        table.setStyle(TableStyle(style))
        return table

    @staticmethod
    def generate_pdf(project_data: Dict,
                     calculations: Dict,
                     materials_db: Dict,
                     logo_base64: Optional[str] = None) -> BytesIO:
        """Genera un PDF del presupuesto."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=1.6 * cm,
            bottomMargin=1.6 * cm,
            leftMargin=1.6 * cm,
            rightMargin=1.6 * cm,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            leading=22,
            textColor=colors.HexColor('#12263A'),
            alignment=TA_LEFT,
            spaceAfter=3,
        )
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#4E5D6C'),
            alignment=TA_LEFT,
            spaceAfter=12,
        )
        section_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontSize=11,
            leading=13,
            textColor=colors.HexColor('#1F3A5F'),
            alignment=TA_LEFT,
            spaceBefore=8,
            spaceAfter=6,
        )
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#2C3E50'),
        )

        story = []

        # Encabezado con logo + datos de emisión
        header_left = []
        if logo_base64:
            try:
                logo_bytes = base64.b64decode(logo_base64)
                logo_buffer = BytesIO(logo_bytes)
                header_left.append(Image(logo_buffer, width=2.4 * cm, height=2.4 * cm, kind='proportional'))
            except Exception:
                pass
        header_left.append(Paragraph("<b>PRESUPUESTO</b>", title_style))
        header_left.append(Paragraph("Carpintería a medida", subtitle_style))

        issue_date = datetime.now().strftime('%d/%m/%Y')
        project_date = project_data.get('date', datetime.now())
        if isinstance(project_date, datetime):
            project_date = project_date.strftime('%d/%m/%Y')
        else:
            project_date = issue_date

        header_right_text = (
            f"<b>Fecha de emisión:</b> {issue_date}<br/>"
            f"<b>Fecha proyecto:</b> {project_date}<br/>"
            f"<b>Estado:</b> {project_data.get('status', 'Activo')}"
        )
        header_data = [[header_left, Paragraph(header_right_text, ParagraphStyle('HR', parent=normal_style, alignment=TA_RIGHT))]]
        header_table = Table(header_data, colWidths=[11.5 * cm, 5.1 * cm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LINEBELOW', (0, 0), (-1, 0), 0.8, colors.HexColor('#1F3A5F')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 0.35 * cm))

        # Datos del cliente/proyecto
        client_data = [
            ['Cliente', project_data.get('client', '—')],
            ['Proyecto', project_data.get('name', '—')],
        ]
        client_table = Table(client_data, colWidths=[3.2 * cm, 13.4 * cm])
        client_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F1F5F9')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#12263A')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#D0D7DE')),
        ]))
        story.append(client_table)
        story.append(Spacer(1, 0.45 * cm))

        # Materiales
        story.append(Paragraph("1. Materiales", section_style))
        material_data = [['Material', 'm² con desperdicio', 'Tablas', 'Importe']] if calculations['material_costs'] else [['Material', 'm² con desperdicio', 'Tablas', 'Importe'], ['Sin materiales', '-', '-', '0.00 €']]

        for material_key, cost_data in calculations['material_costs'].items():
            material_info = materials_db.get(material_key, {})
            material_name = f"{material_info.get('type', material_key)} {material_info.get('color', '')} {material_info.get('thickness_mm', '')}mm".strip()
            material_data.append([
                material_name,
                f"{cost_data['m2_con_desperdicio']:.2f}",
                str(cost_data['boards_needed']),
                f"{cost_data['material_cost']:.2f} €",
            ])

        materials_table = PDFService._create_table(material_data, [8.8 * cm, 3.1 * cm, 2.2 * cm, 2.5 * cm])
        materials_table.setStyle(TableStyle([
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ]),)
        story.append(materials_table)
        story.append(Spacer(1, 0.3 * cm))

        material_total = sum(cost['material_cost'] for cost in calculations['material_costs'].values())

        # Otros conceptos
        story.append(Paragraph("2. Servicios y mano de obra", section_style))
        service_data = [
            ['Concepto', 'Importe'],
            ['Corte y canto', f"{calculations['cutting_cost']:.2f} €"],
            ['Mano de obra y montaje', f"{calculations['labor_for_invoice']:.2f} €"],
        ]
        services_table = PDFService._create_table(service_data, [14.1 * cm, 2.5 * cm])
        services_table.setStyle(TableStyle([
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ]))
        story.append(services_table)

        if calculations['hardware_total'] > 0:
            story.append(Spacer(1, 0.3 * cm))
            story.append(Paragraph("3. Herrajes", section_style))
            hardware_data = [['Concepto', 'Cant.', 'P. unitario', 'Importe']]
            for hardware in project_data.get('hardwares', []):
                quantity = hardware.get('quantity', 0)
                price = hardware.get('price_unit', 0.0)
                total = quantity * price
                if quantity <= 0:
                    continue
                hardware_data.append([
                    hardware.get('type', 'Herraje'),
                    str(quantity),
                    f"{price:.2f} €",
                    f"{total:.2f} €",
                ])
            if len(hardware_data) == 1:
                hardware_data.append(['Sin herrajes', '-', '-', '0.00 €'])
            hardware_table = PDFService._create_table(hardware_data, [9.6 * cm, 2.0 * cm, 2.4 * cm, 2.6 * cm])
            hardware_table.setStyle(TableStyle([
                ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ]))
            story.append(hardware_table)

        story.append(Spacer(1, 0.55 * cm))

        # Resumen final
        cutting_cost = calculations['cutting_cost']
        hardware_total = calculations['hardware_total']
        labor_total = calculations['labor_for_invoice']
        final_price = calculations['final_price']

        summary_data = [
            ['Resumen económico', 'Importe'],
            ['Subtotal materiales', f"{material_total:.2f} €"],
            ['Subtotal corte y canto', f"{cutting_cost:.2f} €"],
            ['Subtotal herrajes', f"{hardware_total:.2f} €"],
            ['Mano de obra y montaje', f"{labor_total:.2f} €"],
            ['TOTAL PRESUPUESTADO', f"{final_price:.2f} €"],
        ]
        summary_table = Table(summary_data, colWidths=[11.6 * cm, 5.0 * cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#12263A')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9.5),
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -2), 9),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#1E8449')),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 11),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#D0D7DE')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#F8FAFC')]),
        ]))
        story.append(summary_table)

        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph(
            "<b>Condiciones:</b> Presupuesto válido por 15 días. Incluye fabricación y montaje según especificaciones del proyecto.",
            normal_style,
        ))

        doc.build(story)
        buffer.seek(0)
        return buffer
