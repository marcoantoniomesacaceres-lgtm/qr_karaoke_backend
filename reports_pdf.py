from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from io import BytesIO
from datetime import datetime

class PDFReportGenerator:
    def __init__(self, title):
        self.buffer = BytesIO()
        self.doc = SimpleDocTemplate(self.buffer, pagesize=letter)
        self.elements = []
        self.styles = getSampleStyleSheet()
        self.title = title

    def add_header(self):
        # APA-style-ish header
        title_style = self.styles['Title']
        title_style.fontName = 'Times-Bold'
        title_style.fontSize = 16
        
        # Centered Title
        self.elements.append(Paragraph("LA CANTA QUE RANA", title_style))
        self.elements.append(Paragraph(f"Reporte: {self.title}", title_style))
        
        # Date
        date_style = self.styles['Normal']
        date_style.alignment = 1 # Center
        self.elements.append(Paragraph(f"Fecha de Generación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", date_style))
        
        self.elements.append(Spacer(1, 0.5 * inch))

    def add_table(self, data, headers):
        if not data:
            self.elements.append(Paragraph("No hay datos disponibles para este reporte.", self.styles['Normal']))
            return

        # Prepare table data
        table_data = [headers] + data

        # Create Table
        # We let reportlab calculate column widths automatically or we could specify them
        t = Table(table_data)

        # Add style (Excel-like grid with borders)
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.2, 0.2, 0.2)), # Dark header
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black), # All borders
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (1, -1), [colors.whitesmoke, colors.white]), # Alternating rows
        ])
        t.setStyle(style)
        self.elements.append(t)

    def add_text(self, text):
        self.elements.append(Spacer(1, 0.2 * inch))
        self.elements.append(Paragraph(text, self.styles['Normal']))

    def generate(self):
        self.add_header()
        self.doc.build(self.elements)
        self.buffer.seek(0)
        return self.buffer
