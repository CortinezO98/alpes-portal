from io import BytesIO
from html import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


PAGE_WIDTH, PAGE_HEIGHT = A4
PRIMARY = colors.HexColor("#176b68")
PRIMARY_DARK = colors.HexColor("#125b57")
PRIMARY_SOFT = colors.HexColor("#e8f0ef")
ACCENT = colors.HexColor("#c69a45")
TEXT = colors.HexColor("#333333")
MUTED = colors.HexColor("#687873")
BORDER = colors.HexColor("#c8d8d6")
SURFACE = colors.HexColor("#f7f4ec")


def _safe(value):
    if value is None:
        return ""
    text = str(value)
    replacements = {
        "—": "-",
        "–": "-",
        "“": '"',
        "”": '"',
        "’": "'",
        "•": "-",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    return text.encode("latin-1", "replace").decode("latin-1")


def _p(value, style):
    return Paragraph(escape(_safe(value)).replace("\n", "<br/>"), style)


def _labeled(label, value, style):
    safe_label = escape(_safe(label))
    safe_value = escape(_safe(value)).replace("\n", "<br/>")
    return Paragraph(f"<b>{safe_label}:</b> {safe_value}", style)


def _date(value):
    if not value:
        return "Pendiente"
    return _safe(value).replace("T", " ")[:16]


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "AlpesTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=PRIMARY_DARK,
            spaceAfter=5 * mm,
        ),
        "subtitle": ParagraphStyle(
            "AlpesSubtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=MUTED,
        ),
        "section": ParagraphStyle(
            "AlpesSection",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=PRIMARY_DARK,
            spaceBefore=5 * mm,
            spaceAfter=3 * mm,
        ),
        "subsection": ParagraphStyle(
            "AlpesSubsection",
            parent=base["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=12,
            textColor=TEXT,
            spaceBefore=2 * mm,
            spaceAfter=1.5 * mm,
        ),
        "body": ParagraphStyle(
            "AlpesBody",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=TEXT,
            spaceAfter=2 * mm,
        ),
        "small": ParagraphStyle(
            "AlpesSmall",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7,
            leading=9,
            textColor=MUTED,
        ),
        "label": ParagraphStyle(
            "AlpesLabel",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=6.5,
            leading=8,
            textColor=MUTED,
            uppercase=True,
        ),
        "center": ParagraphStyle(
            "AlpesCenter",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            alignment=TA_CENTER,
            textColor=PRIMARY_DARK,
        ),
    }


def _page(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.4)
    canvas.line(18 * mm, 15 * mm, PAGE_WIDTH - 18 * mm, 15 * mm)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(18 * mm, 9 * mm, "ALPES - Documento generado desde la plataforma")
    canvas.drawRightString(PAGE_WIDTH - 18 * mm, 9 * mm, f"Pagina {doc.page}")
    canvas.restoreState()


def _meta_table(rows, styles):
    data = []
    for label, value in rows:
        data.append([
            _p(label, styles["label"]),
            _p(value or "-", styles["body"]),
        ])
    table = Table(data, colWidths=[42 * mm, 118 * mm], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), PRIMARY_SOFT),
        ("BOX", (0, 0), (-1, -1), 0.35, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


def _score_table(dimensions, styles):
    data = [[
        _p("Dimension", styles["label"]),
        _p("Resultado", styles["label"]),
        _p("Lectura profesional", styles["label"]),
    ]]
    for dimension in dimensions:
        appreciation = dimension.get("appreciation") or {}
        data.append([
            _p(dimension.get("name", ""), styles["body"]),
            _p(
                f"{dimension.get('average', '-')}/10 - {dimension.get('band_label', '')}",
                styles["body"],
            ),
            _p(appreciation.get("interpretation") or "Sin apreciacion registrada.", styles["small"]),
        ])
    table = Table(data, colWidths=[46 * mm, 34 * mm, 80 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.35, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


def _dream_tree(nodes):
    by_id = {
        node.get("id"): {**node, "children": []}
        for node in (nodes or [])
        if node.get("id") is not None
    }
    roots = []
    for node in by_id.values():
        parent = by_id.get(node.get("parent_id"))
        if parent is not None and parent is not node:
            parent["children"].append(node)
        else:
            roots.append(node)
    return roots


def _append_dream_tree(story, nodes, styles, level=0):
    indent = min(level, 5) * 6 * mm
    for node in nodes:
        type_label = node.get("type_label", "")
        title = node.get("title", "")
        description = node.get("description", "")
        priority = node.get("priority_label", "")
        target_date = node.get("target_date")

        card_data = [[
            _p(type_label or "Elemento", styles["label"]),
            _p(title, styles["subsection"]),
        ]]
        if description:
            card_data.append([
                _p("", styles["small"]),
                _p(description, styles["small"]),
            ])
        meta_parts = []
        if priority:
            meta_parts.append(f"Prioridad: {priority}")
        if target_date:
            meta_parts.append(f"Fecha objetivo: {_date(target_date)}")
        if meta_parts:
            card_data.append([
                _p("", styles["small"]),
                _p(" · ".join(meta_parts), styles["small"]),
            ])

        table = Table(
            card_data,
            colWidths=[24 * mm, max(80 * mm, 136 * mm - indent)],
            hAlign="LEFT",
        )
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), SURFACE),
            ("BOX", (0, 0), (-1, -1), 0.35, BORDER),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        wrapper = Table([[Spacer(indent, 1), table]], colWidths=[indent, 160 * mm - indent])
        wrapper.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 1.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
        ]))
        story.append(wrapper)
        if node.get("children"):
            _append_dream_tree(story, node["children"], styles, level + 1)


def build_individual_report_pdf(report_version):
    styles = _styles()
    snapshot = report_version.snapshot or {}
    participant = snapshot.get("participant") or {}
    engagement = snapshot.get("engagement") or {}
    assessment = snapshot.get("assessment") or {}
    assessment_report = assessment.get("report") or {}

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=17 * mm,
        bottomMargin=20 * mm,
        title=f"Reporte individual v{report_version.version}",
        author="ALPES",
    )
    story = []

    story.append(_p("ALPES", styles["center"]))
    story.append(Spacer(1, 2 * mm))
    story.append(_p("Reporte individual - Jubilacion Plena", styles["title"]))
    story.append(_p(
        f"Version {report_version.version} · generado {_date(report_version.created_at.isoformat())}",
        styles["subtitle"],
    ))
    story.append(Spacer(1, 4 * mm))
    story.append(_meta_table([
        ("Participante", participant.get("name") or participant.get("email")),
        ("Correo", participant.get("email")),
        ("Organizacion", engagement.get("organization") or "Acompanamiento individual"),
        ("Programa", engagement.get("program")),
        ("Proceso", engagement.get("title")),
        ("Consultor", engagement.get("consultant")),
        ("Avance registrado", f"{snapshot.get('progress_percent', 0)}%"),
    ], styles))

    story.append(_p("1. Resumen ejecutivo", styles["section"]))
    story.append(_p(report_version.executive_summary, styles["body"]))

    dimensions = assessment_report.get("dimensions") or []
    if dimensions:
        story.append(_p("2. Rueda de la Vida y lectura profesional", styles["section"]))
        story.append(_score_table(dimensions, styles))

    phases = snapshot.get("phases") or []
    section_number = 3
    for phase in phases:
        if phase.get("code") == "reporte-individual":
            continue
        story.append(_p(
            f"{section_number}. {phase.get('name', 'Fase')}",
            styles["section"],
        ))
        story.append(_p(
            f"Estado: {phase.get('status_label', '')} · Inicio: {_date(phase.get('started_at'))} · Cierre: {_date(phase.get('completed_at'))}",
            styles["small"],
        ))

        consultant_experience = phase.get("consultant_experience") or {}
        if consultant_experience:
            story.append(_p("Registro de la charla", styles["subsection"]))
            story.append(_p(
                f"Fecha: {_date(consultant_experience.get('date'))} · Tema: {consultant_experience.get('topic', '')}",
                styles["small"],
            ))
            for label, key in (
                ("Experiencia y contenido compartido", "consultant_experience"),
                ("Aprendizajes del participante", "participant_learnings"),
                ("Compromisos", "commitments"),
                ("Apreciacion del consultor", "consultant_appreciation"),
            ):
                if consultant_experience.get(key):
                    story.append(_labeled(
                        label,
                        consultant_experience.get(key),
                        styles["body"],
                    ))

        sessions = phase.get("sessions") or []
        if sessions:
            story.append(_p("Sesiones registradas", styles["subsection"]))
            for idx, session in enumerate(sessions, start=1):
                block = [
                    _p(f"Sesion {idx}: {session.get('title', '')}", styles["subsection"]),
                    _p(f"Fecha: {_date(session.get('date'))}", styles["small"]),
                ]
                for label, key in (
                    ("Temas", "topics"),
                    ("Hallazgos", "findings"),
                    ("Compromisos", "commitments"),
                    ("Apreciacion del consultor", "consultant_appreciation"),
                ):
                    if session.get(key):
                        block.append(_labeled(label, session.get(key), styles["body"]))
                story.append(KeepTogether(block))

        nodes = phase.get("nodes") or []
        if nodes:
            story.append(_p("Mapa de retos y suenos", styles["subsection"]))
            root_box = Table(
                [[_p("Mi nueva etapa", styles["center"])]],
                colWidths=[55 * mm],
                hAlign="LEFT",
            )
            root_box.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), PRIMARY),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.35, PRIMARY_DARK),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(root_box)
            story.append(Spacer(1, 2 * mm))
            _append_dream_tree(story, _dream_tree(nodes), styles)

        goals = phase.get("goals") or []
        if goals:
            story.append(_p("Plan de accion", styles["subsection"]))
            for idx, goal in enumerate(goals, start=1):
                story.append(_p(f"Meta {idx}: {goal.get('title', '')}", styles["subsection"]))
                if goal.get("description"):
                    story.append(_p(goal.get("description"), styles["body"]))
                for item in goal.get("items") or []:
                    story.append(_p(
                        f"- {item.get('action', '')} · {item.get('status_label', '')}"
                        + (f" · Indicador: {item.get('indicator')}" if item.get("indicator") else ""),
                        styles["body"],
                    ))

        comments = phase.get("comments") or []
        if comments:
            story.append(_p("Apreciaciones de la fase", styles["subsection"]))
            for comment in comments:
                story.append(_labeled(
                    comment.get("author", ""),
                    comment.get("body", ""),
                    styles["body"],
                ))

        artifacts = phase.get("artifacts") or []
        if artifacts:
            story.append(_p("Soportes registrados", styles["subsection"]))
            for artifact in artifacts:
                story.append(_p(
                    f"- {artifact.get('name', '')}"
                    + (f" ({artifact.get('description')})" if artifact.get("description") else ""),
                    styles["small"],
                ))
        section_number += 1

    story.append(PageBreak())
    story.append(_p(f"{section_number}. Apreciacion integral", styles["section"]))
    story.append(_p(report_version.integral_appreciation, styles["body"]))
    story.append(_p(f"{section_number + 1}. Recomendaciones", styles["section"]))
    story.append(_p(report_version.recommendations, styles["body"]))
    story.append(_p(f"{section_number + 2}. Conclusiones", styles["section"]))
    story.append(_p(report_version.conclusions, styles["body"]))

    doc.build(story, onFirstPage=_page, onLaterPages=_page)
    return buffer.getvalue()


def build_organizational_report_pdf(report_version):
    styles = _styles()
    snapshot = report_version.snapshot or {}
    engagement = snapshot.get("engagement") or {}
    participants = snapshot.get("participants") or {}

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=17 * mm,
        bottomMargin=20 * mm,
        title=f"Reporte organizacional v{report_version.version}",
        author="ALPES",
    )
    story = []

    story.append(_p("ALPES", styles["center"]))
    story.append(Spacer(1, 2 * mm))
    story.append(_p("Reporte organizacional - Jubilacion Plena", styles["title"]))
    story.append(_p(
        f"Version {report_version.version} · generado {_date(report_version.created_at.isoformat())}",
        styles["subtitle"],
    ))
    story.append(Spacer(1, 4 * mm))
    story.append(_meta_table([
        ("Organizacion", engagement.get("organization")),
        ("Programa", engagement.get("program")),
        ("Proceso", engagement.get("title")),
        ("Consultor", engagement.get("consultant")),
        ("Participantes", participants.get("total")),
        ("Evaluaciones completadas", participants.get("completed_assessments")),
        ("Reportes individuales", participants.get("completed_individual_reports")),
    ], styles))

    story.append(_p("1. Resumen ejecutivo", styles["section"]))
    story.append(_p(report_version.executive_summary, styles["body"]))

    dimensions = snapshot.get("dimension_averages") or []
    if dimensions:
        story.append(_p("2. Resultados agregados por dimension", styles["section"]))
        data = [[
            _p("Dimension", styles["label"]),
            _p("Promedio", styles["label"]),
            _p("Participantes", styles["label"]),
        ]]
        for item in dimensions:
            data.append([
                _p(item.get("name"), styles["body"]),
                _p(f"{item.get('average')}/10", styles["body"]),
                _p(item.get("participants"), styles["body"]),
            ])
        table = Table(data, colWidths=[92 * mm, 34 * mm, 34 * mm], repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("BOX", (0, 0), (-1, -1), 0.35, BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, BORDER),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(table)

    story.append(_p("3. Avance agregado del programa", styles["section"]))
    for phase in snapshot.get("phase_summary") or []:
        statuses = phase.get("statuses") or {}
        summary = ", ".join(f"{key}: {value}" for key, value in statuses.items()) or "Sin registros"
        story.append(_labeled(
            f"{phase.get('order')}. {phase.get('name')}",
            summary,
            styles["body"],
        ))

    story.append(_p("4. Apreciacion organizacional", styles["section"]))
    story.append(_p(report_version.organizational_appreciation, styles["body"]))
    story.append(_p("5. Recomendaciones", styles["section"]))
    story.append(_p(report_version.recommendations, styles["body"]))
    story.append(_p("6. Conclusiones", styles["section"]))
    story.append(_p(report_version.conclusions, styles["body"]))

    privacy_note = snapshot.get("privacy_note")
    if privacy_note:
        story.append(Spacer(1, 5 * mm))
        privacy = Table(
            [[_p("Privacidad", styles["label"]), _p(privacy_note, styles["small"])]],
            colWidths=[28 * mm, 132 * mm],
        )
        privacy.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), PRIMARY_SOFT),
            ("BOX", (0, 0), (-1, -1), 0.35, BORDER),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(privacy)

    doc.build(story, onFirstPage=_page, onLaterPages=_page)
    return buffer.getvalue()
