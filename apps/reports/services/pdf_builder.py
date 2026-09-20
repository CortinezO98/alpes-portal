from io import BytesIO
from html import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    CondPageBreak,
    KeepTogether,
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


def _link_p(label, url, style):
    safe_label = escape(_safe(label))
    safe_url = escape(_safe(url), quote=True)
    return Paragraph(
        f'<link href="{safe_url}" color="#176b68"><u>{safe_label}</u></link>',
        style,
    )


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
        "table_header": ParagraphStyle(
            "AlpesTableHeader",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=6.5,
            leading=8,
            textColor=colors.white,
        ),
        "band_green": ParagraphStyle(
            "AlpesBandGreen",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=9,
            textColor=colors.HexColor("#245f3b"),
        ),
        "band_yellow": ParagraphStyle(
            "AlpesBandYellow",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=9,
            textColor=colors.HexColor("#6e5318"),
        ),
        "band_red": ParagraphStyle(
            "AlpesBandRed",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=9,
            textColor=colors.HexColor("#8d3030"),
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
        _p("Dimension", styles["table_header"]),
        _p("Resultado", styles["table_header"]),
        _p("Lectura profesional", styles["table_header"]),
    ]]
    row_bands = []
    for dimension in dimensions:
        appreciation = dimension.get("appreciation") or {}
        band = (dimension.get("band_label") or "").strip().lower()
        if band == "verde":
            band_style = styles["band_green"]
            band_bg = colors.HexColor("#dcefe2")
        elif band == "amarillo":
            band_style = styles["band_yellow"]
            band_bg = colors.HexColor("#f7edca")
        elif band == "rojo":
            band_style = styles["band_red"]
            band_bg = colors.HexColor("#f3d8d8")
        else:
            band_style = styles["body"]
            band_bg = SURFACE
        data.append([
            _p(dimension.get("name", ""), styles["body"]),
            _p(
                f"{dimension.get('average', '-')}/10 - {dimension.get('band_label', '')}",
                band_style,
            ),
            _p(appreciation.get("interpretation") or "Sin apreciacion registrada.", styles["small"]),
        ])
        row_bands.append(band_bg)

    table = Table(data, colWidths=[46 * mm, 34 * mm, 80 * mm], repeatRows=1)
    table_style = [
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("BOX", (0, 0), (-1, -1), 0.35, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for row_index, band_bg in enumerate(row_bands, start=1):
        table_style.append(("BACKGROUND", (1, row_index), (1, row_index), band_bg))
    table.setStyle(TableStyle(table_style))
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


def _dream_type_color(node_type):
    return {
        "DREAM": PRIMARY,
        "CHALLENGE": ACCENT,
        "GOAL": colors.HexColor("#527b78"),
        "MILESTONE": PRIMARY_DARK,
    }.get(node_type, PRIMARY)


def _dream_node_card(node, styles, level=0):
    indent = min(level, 4) * 7 * mm
    stripe = _dream_type_color(node.get("type"))
    description = node.get("description") or ""
    meta_parts = []
    if node.get("priority_label"):
        meta_parts.append(f"Prioridad: {node.get('priority_label')}")
    if node.get("target_date"):
        raw_date = str(node.get("target_date"))
        if len(raw_date) >= 10 and raw_date[4:5] == "-":
            raw_date = f"{raw_date[8:10]}/{raw_date[5:7]}/{raw_date[:4]}"
        meta_parts.append(f"Fecha objetivo: {raw_date}")

    content = [
        _p(node.get("type_label") or "Elemento", styles["label"]),
        _p(node.get("title") or "", styles["subsection"]),
    ]
    if description:
        content.append(_p(description, styles["small"]))
    if meta_parts:
        content.append(_p(" · ".join(meta_parts), styles["small"]))

    card = Table(
        [[Spacer(3 * mm, 1), content]],
        colWidths=[3 * mm, 151 * mm - indent],
        hAlign="LEFT",
    )
    card.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), stripe),
        ("BACKGROUND", (1, 0), (1, -1), SURFACE),
        ("BOX", (0, 0), (-1, -1), 0.35, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, -1), 0),
        ("RIGHTPADDING", (0, 0), (0, -1), 0),
        ("TOPPADDING", (0, 0), (0, -1), 0),
        ("BOTTOMPADDING", (0, 0), (0, -1), 0),
        ("LEFTPADDING", (1, 0), (1, -1), 7),
        ("RIGHTPADDING", (1, 0), (1, -1), 7),
        ("TOPPADDING", (1, 0), (1, -1), 5),
        ("BOTTOMPADDING", (1, 0), (1, -1), 5),
    ]))

    wrapper = Table(
        [[Spacer(indent, 1), card]],
        colWidths=[indent, 154 * mm - indent],
        hAlign="LEFT",
    )
    wrapper.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2),
    ]))
    return wrapper


def _dream_branch_flowables(node, styles, level=0):
    flowables = [_dream_node_card(node, styles, level)]
    for child in node.get("children") or []:
        flowables.extend(_dream_branch_flowables(child, styles, level + 1))
    return flowables


def _append_dream_tree(story, nodes, styles):
    for root in nodes:
        story.append(CondPageBreak(72 * mm))
        story.append(KeepTogether(_dream_branch_flowables(root, styles)))
        story.append(Spacer(1, 2 * mm))


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
        story.append(CondPageBreak(34 * mm))
        story.append(KeepTogether([
            _p(
                f"{section_number}. {phase.get('name', 'Fase')}",
                styles["section"],
            ),
            _p(
                f"Estado: {phase.get('status_label', '')} · Inicio: {_date(phase.get('started_at'))} · Cierre: {_date(phase.get('completed_at'))}",
                styles["small"],
            ),
        ]))

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
            story.append(Spacer(1, 3 * mm))
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
                label = artifact.get("name", "")
                if artifact.get("description"):
                    label += f" ({artifact.get('description')})"
                if artifact.get("absolute_url"):
                    story.append(_link_p(f"Abrir soporte: {label}", artifact.get("absolute_url"), styles["small"]))
                else:
                    story.append(_p(f"- {label}", styles["small"]))
        section_number += 1

    story.append(CondPageBreak(58 * mm))
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
