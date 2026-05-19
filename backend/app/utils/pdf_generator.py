import io
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def generate_trend_chart(days, scores):
    """Generates a trend chart and returns it as a BytesIO object."""
    plt.figure(figsize=(6, 3))
    plt.plot(days, scores, marker='o', linestyle='-', color='#1f77b4')
    plt.title('Tren Skor Gizi Mingguan')
    plt.xlabel('Tanggal')
    plt.ylabel('Skor Gizi')
    plt.ylim(0, 100)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    img_bytes = io.BytesIO()
    plt.savefig(img_bytes, format='png', dpi=300)
    plt.close()
    img_bytes.seek(0)
    return img_bytes

def create_weekly_report_pdf(data: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    
    # 1. Header
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], alignment=1) # Center
    elements.append(Paragraph(f"Laporan Mingguan Gizi - {data['sppg_name']}", title_style))
    elements.append(Paragraph(f"Distrik/Kota: {data['district']}", styles['Normal']))
    elements.append(Paragraph(f"Periode: {data['period']}", styles['Normal']))
    elements.append(Spacer(1, 0.2 * inch))

    # 2. Daily Menu Table
    table_data = [['Tanggal', 'Menu', 'Skor Gizi', 'Status']]
    for day in data['daily_menus']:
        status = day['status']
        table_data.append([day['date'], day['menu'], str(day['score']), status])
        
    # Table styling with dynamic color coding
    t = Table(table_data, colWidths=[1.2*inch, 2.5*inch, 1*inch, 1.5*inch])
    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#d3d3d3')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]
    
    # Add color coding to status rows
    for i, row in enumerate(data['daily_menus'], start=1):
        if row['status'] == 'Cukup':
            bg_color = colors.HexColor('#d4edda') # Green
        elif row['status'] == 'Perlu Perhatian':
            bg_color = colors.HexColor('#fff3cd') # Yellow
        else:
            bg_color = colors.HexColor('#f8d7da') # Red
        table_style.append(('BACKGROUND', (3, i), (3, i), bg_color))

    t.setStyle(TableStyle(table_style))
    elements.append(t)
    elements.append(Spacer(1, 0.3 * inch))

    # 3. Trend Chart
    days = [d['date'][-5:] for d in data['daily_menus']] # Just MM-DD for x-axis
    scores = [d['score'] for d in data['daily_menus']]
    chart_img = generate_trend_chart(days, scores)
    elements.append(Image(chart_img, width=6*inch, height=3*inch))
    elements.append(Spacer(1, 0.3 * inch))

    # 4. Top Deficiencies
    elements.append(Paragraph("Top 3 Komponen Gizi Defisien", styles['Heading3']))
    for item in data['top_deficiencies']:
        elements.append(Paragraph(f"• {item}", styles['Normal']))
    elements.append(Spacer(1, 0.2 * inch))

    # 5. Recommendations
    elements.append(Paragraph("3 Prioritas Rekomendasi Perbaikan", styles['Heading3']))
    for idx, rec in enumerate(data['recommendations'], start=1):
        elements.append(Paragraph(f"{idx}. {rec}", styles['Normal']))

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes