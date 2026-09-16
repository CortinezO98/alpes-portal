from django.core.management.base import BaseCommand
from django.db import transaction

from apps.assessments.models import AssessmentTemplate, Dimension, Question
from apps.assessments.services.template_versioning import publish_template


DIMENSIONS = (
    (
        "proposito-motivacion",
        "Propósito y Motivación",
        (
            "Tengo claro cual es mi propósito principal en esta nueva etapa de mi vida.",
            "Me siento motivado (a) para explorar nuevas actividades o proyectos.",
            "Creo que esta etapa representa una oportunidad para alcanzar metas personales.",
            "Estoy entusiasmado(a) por descubrir nuevos intereses o pasiones.",
        ),
    ),
    (
        "relaciones-interpersonales",
        "Relaciones Interpersonales",
        (
            "Me siento satisfecho(a) con la calidad de mis relaciones personales (familia, amigos, comunidad).",
            "Tengo una red de apoyo emocional en la que puedo confiar.",
            "Estoy dispuesto(a) a fortalecer mis relaciones actuales y crear nuevas conexiones.",
            "Considero que mis relaciones contribuirán positivamente a mi bienestar en esta etapa.",
        ),
    ),
    (
        "salud-fisica-bienestar",
        "Salud Física y Bienestar",
        (
            "Estoy satisfecho(a) con mi estado de salud físico actual.",
            "Estoy comprometido(a) a mantener hábitos saludables para cuidar mi bienestar.",
            "Considero que mi nivel de energía física es adecuado para disfrutar de esta nueva etapa.",
            "Estoy dispuesto(a) a realizar cambios en mi estilo de vida para mejorar mi salud.",
        ),
    ),
    (
        "salud-emocional-mental",
        "Salud Emocional y Mental",
        (
            "Me siento emocionalmente preparado(a) para enfrentar los cambios que trae esta etapa.",
            "Considero que puedo manejar el estrés o la ansiedad relacionados con la jubilación.",
            "Me siento positivo(a) y optimista sobre mi futuro.",
            "Estoy dispuesto(a) a buscar apoyo emocional si lo necesito.",
        ),
    ),
    (
        "finanzas-seguridad-economica",
        "Finanzas y Seguridad Económica",
        (
            "Me siento seguro(a) sobre mi capacidad para administrar mis recursos económicos en la jubilación.",
            "Tengo un plan financiero claro para esta etapa.",
            "Estoy informado(a) sobre las opciones de ahorro o inversión para mi bienestar económico.",
            "Considero que mis ingresos actuales y proyectados son suficientes para mantener mi estilo de vida deseado.",
        ),
    ),
    (
        "tiempo-libre-hobbies",
        "Tiempo Libre y Hobbies",
        (
            "Estoy satisfecho(a) con las actividades que realizo en mi tiempo libre.",
            "Tengo hobbies o intereses que me apasionan y me generan satisfacción.",
            "Estoy dispuesto(a) a probar nuevas actividades recreativas o creativas.",
            "Considero que estoy aprovechando mi tiempo libre de manera equilibrada y significativa.",
        ),
    ),
    (
        "contribucion-comunidad",
        "Contribución y Comunidad",
        (
            "Me siento conectado(a) con mi comunidad o con actividades que beneficien a otros.",
            "Estoy interesado(a) en participar en proyectos o voluntariados.",
            "Considero que contribuir al bienestar de otros me ayudará a sentirme realizado(a).",
            "Estoy dispuesto(a) a dedicar tiempo y energia a causas que me importen.",
        ),
    ),
    (
        "aprendizaje-desarrollo-personal",
        "Aprendizaje y Desarrollo Personal",
        (
            "Estoy interesado(a) en aprender nuevas habilidades o conocimientos en esta etapa.",
            "Creo que esta es una oportunidad para crecer y desarrollarme personalmente.",
            "Estoy dispuesto(a) a salir de mi zona de confort para explorar nuevos desafíos.",
            "Considero que el aprendizaje continuo es esencial para mi bienestar.",
        ),
    ),
)

GENERAL_QUESTIONS = (
    "¿Que sueños o metas te gustaría alcanzar durante esta etapa de tu vida?",
    "¿Hay algo más que te gustaría compartir sobre tus expectativas o preocupaciones respecto a la jubilación?",
    "¿Que esperas encontar en este programa para disfrutar con plenitud esta nueva etapa de tu vida?",
)


class Command(BaseCommand):
    help = "Crea y publica la versión inicial de ALPES - Jubilación Plena de forma segura."

    @transaction.atomic
    def handle(self, *args, **options):
        template, created = AssessmentTemplate.objects.get_or_create(
            slug="alpes-jubilacion-plena",
            defaults={
                "name": "ALPES - Jubilación Plena",
                "is_active": True,
            },
        )

        if not created and not template.is_editable:
            self.stdout.write(
                self.style.WARNING(
                    "La plantilla ya está publicada y no se modificó. "
                    "Para cambiar preguntas o dimensiones, crea una nueva versión."
                )
            )
            return

        template.name = "ALPES - Jubilación Plena"
        template.is_active = True
        template.save(update_fields=("name", "is_active", "updated_at"))

        for dimension_order, (slug, name, statements) in enumerate(DIMENSIONS, start=1):
            dimension, _ = Dimension.objects.update_or_create(
                template=template,
                slug=slug,
                defaults={
                    "name": name,
                    "order": dimension_order,
                },
            )

            for question_order, statement in enumerate(statements, start=1):
                Question.objects.update_or_create(
                    dimension=dimension,
                    order=question_order,
                    defaults={
                        "template": None,
                        "text": statement,
                        "question_type": Question.Type.SCALE,
                        "is_required": True,
                    },
                )

        for question_order, text in enumerate(GENERAL_QUESTIONS, start=1):
            Question.objects.update_or_create(
                template=template,
                dimension=None,
                order=question_order,
                defaults={
                    "text": text,
                    "question_type": Question.Type.TEXT,
                    "is_required": False,
                },
            )

        publish_template(template)
        self.stdout.write(
            self.style.SUCCESS(
                "Plantilla ALPES - Jubilación Plena publicada: "
                "8 dimensiones, 32 preguntas de escala y 3 preguntas abiertas."
            )
        )
