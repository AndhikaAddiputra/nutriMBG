import io
from importlib import import_module
from typing import Iterable


def _load_matplotlib_pyplot():
    try:
        return import_module("matplotlib.pyplot")
    except ModuleNotFoundError:
        return None


def _load_reportlab():
    try:
        pagesizes = import_module("reportlab.lib.pagesizes")
        colors = import_module("reportlab.lib.colors")
        platypus = import_module("reportlab.platypus")
        styles = import_module("reportlab.lib.styles")
        units = import_module("reportlab.lib.units")
    except ModuleNotFoundError:
        return None

    return {
        "A4": pagesizes.A4,
        "colors": colors,
        "SimpleDocTemplate": platypus.SimpleDocTemplate,
        "Paragraph": platypus.Paragraph,
        "Spacer": platypus.Spacer,
        "Table": platypus.Table,
        "TableStyle": platypus.TableStyle,
        "Image": platypus.Image,
        "getSampleStyleSheet": styles.getSampleStyleSheet,
        "ParagraphStyle": styles.ParagraphStyle,
        "inch": units.inch,
    }


plt = _load_matplotlib_pyplot()
_reportlab = _load_reportlab()

def generate_trend_chart(days, scores):
    """Generates a trend chart and returns it as a BytesIO object."""
    if plt is None:
        return None
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


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _wrap_text_lines(text: str, max_length: int = 92) -> list[str]:
    words = text.split()
    if not words:
        return [""]

    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if len(candidate) <= max_length:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _build_minimal_pdf(lines: Iterable[str]) -> bytes:
    content_lines = []
    y = 780
    content_lines.append("BT")
    content_lines.append("/F1 12 Tf")
    for line in lines:
        for segment in _wrap_text_lines(line):
            content_lines.append(f"1 0 0 1 50 {y} Tm")
            content_lines.append(f"({_escape_pdf_text(segment)}) Tj")
            y -= 16
            if y < 60:
                break
        if y < 60:
            break
    content_lines.append("ET")
    content_stream = "\n".join(content_lines).encode("latin-1", errors="replace")

    objects: list[bytes] = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    objects.append(b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    objects.append(b"<< /Length %d >>\nstream\n" % len(content_stream) + content_stream + b"\nendstream")

    pdf = bytearray()
    pdf.extend(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        (
            "trailer\n"
            f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            "startxref\n"
            f"{xref_offset}\n"
            "%%EOF\n"
        ).encode("ascii")
    )
    return bytes(pdf)

def create_weekly_report_pdf(data: dict) -> bytes:
    if _reportlab is None:
        lines = [
            f"Laporan Mingguan Gizi - {data['sppg_name']}",
            f"Distrik/Kota: {data['district']}",
            f"Periode: {data['period']}",
            "",
            "Ringkasan menu mingguan:",
        ]
        for day in data["daily_menus"]:
            lines.append(f"- {day['date']}: {day['menu']} | Skor {day['score']} | {day['status']}")
        lines.append("")
        lines.append("Top 3 Komponen Gizi Defisien:")
        lines.extend([f"- {item}" for item in data["top_deficiencies"]])
        lines.append("")
        lines.append("3 Prioritas Rekomendasi Perbaikan:")
        lines.extend([f"- {rec}" for rec in data["recommendations"]])
        return _build_minimal_pdf(lines)

    A4 = _reportlab["A4"]
    colors = _reportlab["colors"]
    SimpleDocTemplate = _reportlab["SimpleDocTemplate"]
    Paragraph = _reportlab["Paragraph"]
    Spacer = _reportlab["Spacer"]
    Table = _reportlab["Table"]
    TableStyle = _reportlab["TableStyle"]
    Image = _reportlab["Image"]
    getSampleStyleSheet = _reportlab["getSampleStyleSheet"]
    ParagraphStyle = _reportlab["ParagraphStyle"]
    inch = _reportlab["inch"]

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
    if chart_img is not None:
        elements.append(Image(chart_img, width=6*inch, height=3*inch))
        elements.append(Spacer(1, 0.3 * inch))
    else:
        elements.append(Paragraph("Grafik tren tidak ditampilkan karena pustaka visualisasi tidak tersedia.", styles['Italic']))
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