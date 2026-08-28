from django.http import HttpResponse
from django.urls import reverse
from django.views.generic import TemplateView


SERVICE_PAGES = {
    "leadership": {
        "route_name": "portfolio:leadership",
        "number": "01",
        "eyebrow": "Liderazgo",
        "title": "Acompañamiento al Liderazgo de la organización",
        "lead": (
            "Fortalecimiento de habilidades humanas, estratégicas y relacionales, "
            "alineado con la cultura y los objetivos de la organización."
        ),
        "statement": "Liderazgo consciente para culturas y resultados sostenibles.",
        "description": (
            "Un proceso de acompañamiento que parte de la autovaloración, avanza a través "
            "de mentoría y coaching y conecta el desarrollo del líder con las necesidades "
            "reales de su organización."
        ),
        "includes": [
            "Autovaloración de competencias.",
            "4 sesiones individuales de mentoría.",
            "4 sesiones individuales de coaching.",
            "Reporte individual y organizacional.",
        ],
        "audience": (
            "Líderes y organizaciones que buscan fortalecer competencias, relaciones, "
            "cultura y capacidad de gestión."
        ),
        "steps": [
            ("01", "Autovaloración", "Lectura inicial de competencias y oportunidades de desarrollo."),
            ("02", "Mentoría", "Conversaciones orientadas por experiencia, contexto y retos del rol."),
            ("03", "Coaching", "Acompañamiento individual para movilizar decisiones y cambios sostenibles."),
            ("04", "Reporte", "Síntesis de avance con lectura individual y organizacional."),
        ],
        "seo_title": "Acompañamiento al Liderazgo | ALPES",
        "seo_description": (
            "Acompañamiento ALPES para fortalecer liderazgo, competencias humanas, "
            "estrategia, relaciones y cultura organizacional."
        ),
    },
    "retirement": {
        "route_name": "portfolio:retirement",
        "number": "02",
        "eyebrow": "Transición",
        "title": "Jubilación Plena",
        "lead": (
            "Programa para acompañar al personal próximo a pensionarse hacia una nueva "
            "etapa con propósito, bienestar y sentido."
        ),
        "statement": "Una transición consciente hacia una vida con propósito y equilibrio.",
        "description": (
            "Jubilación Plena combina lectura integral, conversaciones transformadoras, "
            "retos y sueños con planes de acción que ayudan a preparar la siguiente etapa "
            "de vida de forma consciente."
        ),
        "includes": [
            "Rueda de la vida para prepensionados.",
            "Conversaciones transformadoras.",
            "Mapa de retos y sueños.",
            "Planes de acción y reportes.",
        ],
        "audience": (
            "Personas próximas a pensionarse y organizaciones que desean acompañar esta "
            "transición con una mirada humana e integral."
        ),
        "steps": [
            ("01", "Rueda de la vida", "Lectura de las dimensiones que componen el bienestar actual."),
            ("02", "Conversaciones", "Reflexión guiada sobre identidad, propósito y nueva etapa."),
            ("03", "Retos y sueños", "Construcción del futuro deseado y sus prioridades."),
            ("04", "Plan de acción", "Definición de compromisos y seguimiento de resultados."),
        ],
        "seo_title": "Jubilación Plena | ALPES",
        "seo_description": (
            "Programa ALPES de Jubilación Plena para acompañar a personas próximas a "
            "pensionarse con propósito, bienestar, retos, sueños y planes de acción."
        ),
    },
    "consulting": {
        "route_name": "portfolio:consulting",
        "number": "03",
        "eyebrow": "Organización",
        "title": "Mentorías y Consultorías Organizacionales",
        "lead": (
            "Acompañamiento para fortalecer procesos que permiten a las organizaciones "
            "alcanzar sus propósitos."
        ),
        "statement": "Experiencia ejecutiva aplicada a retos reales de organización y talento.",
        "description": (
            "La mentoría y consultoría se orienta a conversaciones y procesos concretos de "
            "liderazgo, cultura, desempeño, cambio y gestión de Talento Humano."
        ),
        "includes": [
            "Modelo de liderazgo y cultura organizacional.",
            "Gestión del desempeño y clima.",
            "Gestión del cambio y talento humano.",
            "Relaciones laborales y sindicales.",
        ],
        "audience": (
            "Organizaciones, equipos directivos y áreas de Talento Humano que requieren "
            "acompañamiento en desafíos de personas, cultura y gestión."
        ),
        "steps": [
            ("01", "Contexto", "Comprensión del reto, actores, necesidades y propósito organizacional."),
            ("02", "Lectura", "Análisis del proceso o situación priorizada con el equipo responsable."),
            ("03", "Acompañamiento", "Mentoría o consultoría aplicada a decisiones y acciones concretas."),
            ("04", "Seguimiento", "Revisión de compromisos, aprendizajes y próximos pasos."),
        ],
        "seo_title": "Mentorías y Consultorías Organizacionales | ALPES",
        "seo_description": (
            "Mentoría y consultoría ALPES en liderazgo, cultura, desempeño, clima, cambio, "
            "Talento Humano y relaciones laborales."
        ),
    },
    "alpes": {
        "route_name": "portfolio:model_alpes",
        "number": "04",
        "eyebrow": "Metodología propia",
        "title": "Modelo ALPES",
        "lead": (
            "Una lectura integral de las áreas de vida para concretar retos, sueños "
            "personales y organizacionales, y construir caminos posibles."
        ),
        "statement": "Propósito, bienestar y equilibrio convertidos en un camino de acción.",
        "description": (
            "ALPES analiza la situación actual, ayuda a construir el futuro deseado y "
            "convierte esa visión en planes alcanzables sustentados en responsabilidad, "
            "disciplina y compromiso."
        ),
        "includes": [
            "Análisis de las áreas de la vida.",
            "Mapa de retos y sueños.",
            "Construcción del camino al éxito.",
            "Planes de acción con hitos y compromisos claros.",
        ],
        "audience": (
            "Personas y organizaciones que buscan comprender su situación actual, definir "
            "un futuro deseado y convertirlo en acciones concretas."
        ),
        "steps": [
            ("01", "Análisis de las áreas de la vida", "Lectura integral para identificar oportunidades de mejora."),
            ("02", "Mapa de retos y sueños", "Definición consciente del futuro deseado y sus prioridades."),
            ("03", "Camino al éxito", "Construcción de planes alcanzables con hitos y compromisos claros."),
        ],
        "seo_title": "Modelo ALPES | Propósito, Bienestar y Acción",
        "seo_description": (
            "Conoce el Modelo ALPES: análisis integral, mapa de retos y sueños y un camino "
            "de acción hacia propósito, bienestar y equilibrio."
        ),
    },
}


class PublicHomeView(TemplateView):
    template_name = "portfolio/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "seo_index": True,
                "seo_title": "ALPES | Coaching Directivo, Liderazgo y Transformación",
                "seo_description": (
                    "Portafolio de José Alfonso Marrugo Roa: coaching directivo, liderazgo, "
                    "Jubilación Plena, consultoría organizacional y Modelo ALPES."
                ),
                "seo_canonical": self.request.build_absolute_uri(reverse("portfolio:home")),
            }
        )
        return context


class PublicServiceDetailView(TemplateView):
    template_name = "portfolio/service_detail.html"
    page_key = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = SERVICE_PAGES[self.page_key]
        context.update(
            {
                "service": service,
                "seo_index": True,
                "seo_title": service["seo_title"],
                "seo_description": service["seo_description"],
                "seo_canonical": self.request.build_absolute_uri(reverse(service["route_name"])),
            }
        )
        return context


def robots_txt(request):
    sitemap_url = request.build_absolute_uri(reverse("portfolio:sitemap"))
    content = "\n".join(
        [
            "User-agent: *",
            "Allow: /",
            "Disallow: /admin/",
            "Disallow: /cuenta/",
            "Disallow: /evaluaciones/",
            "Disallow: /reportes/",
            f"Sitemap: {sitemap_url}",
            "",
        ]
    )
    return HttpResponse(content, content_type="text/plain; charset=utf-8")


def sitemap_xml(request):
    pages = [
        ("portfolio:home", "1.0"),
        ("portfolio:leadership", "0.9"),
        ("portfolio:retirement", "0.9"),
        ("portfolio:consulting", "0.9"),
        ("portfolio:model_alpes", "0.9"),
    ]
    entries = []
    for route_name, priority in pages:
        page_url = request.build_absolute_uri(reverse(route_name))
        entries.append(
            "  <url>\n"
            f"    <loc>{page_url}</loc>\n"
            "    <changefreq>monthly</changefreq>\n"
            f"    <priority>{priority}</priority>\n"
            "  </url>"
        )

    content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(entries)
        + "\n</urlset>\n"
    )
    return HttpResponse(content, content_type="application/xml; charset=utf-8")
