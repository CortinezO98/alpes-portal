import pytest
from django.core.management import call_command
from django.urls import reverse

from apps.accounts.models import User
from apps.assessments.forms import AssessmentAssignForm
from apps.assessments.models import Assessment, AssessmentTemplate


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
def test_published_version_edit_route_returns_404(client, template_management_setup):
    superadmin, _, _, version_one = template_management_setup
    dimension = version_one.dimensions.order_by("order").first()
    client.force_login(superadmin)

    response = client.get(
        reverse("assessments:dimension-edit", kwargs={"pk": dimension.pk})
    )

    assert response.status_code == 404
