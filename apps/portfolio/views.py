from django.http import HttpResponse
from django.urls import reverse
from django.views.generic import TemplateView


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
    home_url = request.build_absolute_uri(reverse("portfolio:home"))
    content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        "  <url>\n"
        f"    <loc>{home_url}</loc>\n"
        "    <changefreq>monthly</changefreq>\n"
        "    <priority>1.0</priority>\n"
        "  </url>\n"
        "</urlset>\n"
    )
    return HttpResponse(content, content_type="application/xml; charset=utf-8")
