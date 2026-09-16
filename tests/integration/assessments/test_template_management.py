import pytest
from django.core.management import call_command
from django.urls import reverse

from apps.accounts.models import User
from apps.assessments.forms import AssessmentAssignForm
from apps.assessments.models import Assessment, AssessmentTemplate, Question


@pytest.fixture
def template_management_setup(db):
    call_command("seed_jubilacion_plena")
    template = AssessmentTemplate.objects.get(slug="alpes-jubilacion-plena")
    superadmin = User.objects.create_superuser(
        email="superadmin-templates@example.com",
        password="SecurePass123!",
    )
    admin = User.objects.create_user(
        email="admin-templates@example.com",
        password="SecurePass123!",
        role=User.Role.ADMIN,
        is_staff=True,
    )
    participant = User.objects.create_user(
        email="participant-templates@example.com",
        password="SecurePass123!",
        role=User.Role.USER,
    )
    return superadmin, admin, participant, template


@pytest.mark.django_db
def test_only_superadmin_can_open_template_configuration(client, template_management_setup):
    superadmin, admin, _, template = template_management_setup

    client.force_login(admin)
    denied = client.get(reverse("assessments:template-list"))
    assert denied.status_code == 403

    client.force_login(superadmin)
    allowed = client.get(reverse("assessments:template-list"))
    assert allowed.status_code == 200
    assert template in list(allowed.context["templates"])


@pytest.mark.django_db
def test_new_version_keeps_current_version_published_until_replacement_is_published(
    client,
    template_management_setup,
):
    superadmin, _, participant, version_one = template_management_setup
    historical_assessment = Assessment.objects.create(
        template=version_one,
        participant=participant,
        created_by=superadmin,
    )
    client.force_login(superadmin)

    response = client.post(
        reverse("assessments:template-new-version", kwargs={"pk": version_one.pk})
    )

    assert response.status_code == 302
    version_one.refresh_from_db()
    version_two = version_one.successor_versions.get(version=2)
    assert version_one.publication_status == AssessmentTemplate.PublicationStatus.PUBLISHED
    assert version_one.is_active is True
    assert version_two.publication_status == AssessmentTemplate.PublicationStatus.DRAFT
    assert version_two.is_active is False

    response = client.post(
        reverse("assessments:template-publish", kwargs={"pk": version_two.pk})
    )
    assert response.status_code == 302

    version_one.refresh_from_db()
    version_two.refresh_from_db()
    historical_assessment.refresh_from_db()
    assert version_one.publication_status == AssessmentTemplate.PublicationStatus.RETIRED
    assert version_one.is_active is False
    assert version_two.publication_status == AssessmentTemplate.PublicationStatus.PUBLISHED
    assert version_two.is_active is True
    assert historical_assessment.template_id == version_one.pk

    assignable_ids = list(
        AssessmentAssignForm().fields["template"].queryset.values_list("pk", flat=True)
    )
    assert version_two.pk in assignable_ids
    assert version_one.pk not in assignable_ids


@pytest.mark.django_db
def test_draft_dimension_can_be_changed_from_configuration_ui(
    client,
    template_management_setup,
):
    superadmin, _, _, version_one = template_management_setup
    client.force_login(superadmin)
    client.post(reverse("assessments:template-new-version", kwargs={"pk": version_one.pk}))
    version_two = version_one.successor_versions.get(version=2)
    dimension = version_two.dimensions.order_by("order").first()

    response = client.post(
        reverse("assessments:dimension-edit", kwargs={"pk": dimension.pk}),
        {
            "name": "Propósito renovado",
            "description": "Descripción modificable de la nueva versión.",
            "order": dimension.order,
        },
    )

    assert response.status_code == 302
    dimension.refresh_from_db()
    assert dimension.name == "Propósito renovado"
    assert dimension.slug == "proposito-renovado"
    assert version_one.dimensions.order_by("order").first().name == "Propósito y Motivación"


@pytest.mark.django_db
def test_draft_template_renders_inline_item_controls(client, template_management_setup):
    superadmin, _, _, version_one = template_management_setup
    client.force_login(superadmin)
    client.post(reverse("assessments:template-new-version", kwargs={"pk": version_one.pk}))
    version_two = version_one.successor_versions.get(version=2)

    response = client.get(
        reverse("assessments:template-detail", kwargs={"pk": version_two.pk})
    )
    content = response.content.decode("utf-8")

    assert response.status_code == 200
    assert 'value="update-scale-question"' in content
    assert 'value="create-scale-question"' in content
    assert "+ Agregar ítem en" in content
    assert "Guardar cambios" in content


@pytest.mark.django_db
def test_draft_template_can_create_item_inline_without_changing_published_version(
    client,
    template_management_setup,
):
    superadmin, _, _, version_one = template_management_setup
    client.force_login(superadmin)
    client.post(reverse("assessments:template-new-version", kwargs={"pk": version_one.pk}))
    version_two = version_one.successor_versions.get(version=2)
    draft_dimension = version_two.dimensions.order_by("order").first()
    original_dimension = version_one.dimensions.get(order=draft_dimension.order)
    original_count = original_dimension.questions.count()
    new_order = draft_dimension.questions.count() + 1

    response = client.post(
        reverse("assessments:template-detail", kwargs={"pk": version_two.pk}),
        {
            "action": "create-scale-question",
            "dimension_id": draft_dimension.pk,
            "text": "Nuevo ítem configurable desde la misma vista.",
            "order": new_order,
            "is_required": "on",
        },
    )

    assert response.status_code == 302
    assert Question.objects.filter(
        dimension=draft_dimension,
        text="Nuevo ítem configurable desde la misma vista.",
        order=new_order,
        is_required=True,
    ).exists()
    assert original_dimension.questions.count() == original_count


@pytest.mark.django_db
def test_draft_template_can_update_item_inline_without_changing_published_version(
    client,
    template_management_setup,
):
    superadmin, _, _, version_one = template_management_setup
    client.force_login(superadmin)
    client.post(reverse("assessments:template-new-version", kwargs={"pk": version_one.pk}))
    version_two = version_one.successor_versions.get(version=2)
    draft_dimension = version_two.dimensions.order_by("order").first()
    draft_question = draft_dimension.questions.order_by("order").first()
    original_question = version_one.dimensions.get(order=draft_dimension.order).questions.get(
        order=draft_question.order
    )
    original_text = original_question.text

    response = client.post(
        reverse("assessments:template-detail", kwargs={"pk": version_two.pk}),
        {
            "action": "update-scale-question",
            "question_id": draft_question.pk,
            "text": "Ítem actualizado inline.",
            "order": draft_question.order,
            "is_required": "on",
        },
    )

    assert response.status_code == 302
    draft_question.refresh_from_db()
    original_question.refresh_from_db()
    assert draft_question.text == "Ítem actualizado inline."
    assert original_question.text == original_text


@pytest.mark.django_db
def test_published_version_rejects_inline_item_changes(client, template_management_setup):
    superadmin, _, _, version_one = template_management_setup
    dimension = version_one.dimensions.order_by("order").first()
    client.force_login(superadmin)

    response = client.post(
        reverse("assessments:template-detail", kwargs={"pk": version_one.pk}),
        {
            "action": "create-scale-question",
            "dimension_id": dimension.pk,
            "text": "No debe crearse",
            "order": 99,
            "is_required": "on",
        },
    )

    assert response.status_code == 404
    assert not Question.objects.filter(text="No debe crearse").exists()


@pytest.mark.django_db
def test_published_version_edit_route_returns_404(client, template_management_setup):
    superadmin, _, _, version_one = template_management_setup
    dimension = version_one.dimensions.order_by("order").first()
    client.force_login(superadmin)

    response = client.get(
        reverse("assessments:dimension-edit", kwargs={"pk": dimension.pk})
    )

    assert response.status_code == 404
