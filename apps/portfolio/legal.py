from django.urls import reverse
from django.views.generic import TemplateView


LEGAL_PAGES = {
    "privacy": {
        "title": "Política de privacidad",
        "route_name": "portfolio:privacy",
        "intro": (
            "Esta página describe, de forma informativa, cómo se gestionan los datos personales "
            "en el portal ALPES. La versión definitiva deberá completarse con la identificación "
            "jurídica y los canales formales del responsable antes del despliegue productivo."
        ),
        "sections": [
            (
                "Marco aplicable",
                "El tratamiento de datos personales se orienta por la Constitución Política de Colombia, "
                "la Ley 1581 de 2012, el Decreto 1074 de 2015 y las normas que los modifiquen, adicionen o sustituyan.",
            ),
            (
                "Datos que puede tratar el portal",
                "Datos de identificación y contacto, credenciales de acceso, información asociada a evaluaciones, "
                "respuestas suministradas por los participantes y registros técnicos necesarios para seguridad y auditoría.",
            ),
            (
                "Finalidades",
                "Administrar cuentas y accesos, gestionar evaluaciones y reportes, prestar los servicios ALPES, "
                "atender solicitudes, proteger la plataforma, prevenir abuso y mantener trazabilidad de acciones sensibles.",
            ),
            (
                "Principios de seguridad",
                "El portal aplica controles de acceso por roles, protección de sesiones, límites de intentos de autenticación, "
                "auditoría de eventos sensibles y medidas para reducir la exposición de información técnica.",
            ),
            (
                "Derechos del titular",
                "Los titulares pueden conocer, actualizar y rectificar sus datos; solicitar prueba de la autorización cuando aplique; "
                "ser informados sobre el uso de sus datos; presentar consultas o reclamos y solicitar supresión o revocatoria en los casos permitidos por la ley.",
            ),
            (
                "Canal de atención",
                "El canal formal para consultas, reclamos y ejercicio de derechos de protección de datos será publicado antes del despliegue productivo. "
                "El WhatsApp visible actualmente en el portal es provisional y no debe considerarse todavía el canal jurídico definitivo.",
            ),
        ],
    },
    "data_treatment": {
        "title": "Tratamiento de datos personales",
        "route_name": "portfolio:data-treatment",
        "intro": (
            "Resumen operativo del tratamiento de información dentro de ALPES. Este contenido se publica como borrador técnico "
            "y deberá ser revisado junto con la identificación y política definitiva del responsable del tratamiento."
        ),
        "sections": [
            (
                "Autorización y transparencia",
                "Cuando sea exigible, el tratamiento deberá contar con autorización previa, expresa e informada del titular, "
                "explicando las finalidades y los derechos que le asisten.",
            ),
            (
                "Información de evaluaciones",
                "Las respuestas, resultados y reportes de las evaluaciones se utilizan exclusivamente para los procesos de acompañamiento, "
                "seguimiento y análisis autorizados dentro de la plataforma y se restringen según el rol del usuario.",
            ),
            (
                "Acceso y confidencialidad",
                "Los usuarios solo deben acceder a la información necesaria para sus funciones. Los roles administrativos se encuentran separados "
                "de los participantes y las acciones sensibles quedan sujetas a trazabilidad.",
            ),
            (
                "Conservación",
                "Los datos deben conservarse únicamente durante el tiempo necesario para cumplir las finalidades informadas, obligaciones contractuales o legales, "
                "y posteriormente eliminarse, anonimizarse o bloquearse según corresponda.",
            ),
            (
                "Datos sensibles",
                "Si una evaluación o proceso llegara a involucrar datos sensibles, su tratamiento requerirá controles reforzados y, cuando corresponda, autorización explícita del titular. "
                "La participación no debe condicionarse al suministro de datos sensibles salvo que exista fundamento legal y necesidad legítima.",
            ),
            (
                "Consultas y reclamos",
                "La versión productiva deberá informar el responsable del tratamiento, su identificación, dirección o canal electrónico, correo de contacto y procedimiento para consultas y reclamos.",
            ),
        ],
    },
}


class PublicLegalView(TemplateView):
    template_name = "portfolio/legal.html"
    page_key = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page = LEGAL_PAGES[self.page_key]
        context.update(
            {
                "legal_page": page,
                "seo_index": False,
                "seo_title": f"{page['title']} | ALPES",
                "seo_description": page["intro"],
                "seo_canonical": self.request.build_absolute_uri(reverse(page["route_name"])),
            }
        )
        return context
