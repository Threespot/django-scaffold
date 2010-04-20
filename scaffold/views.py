from django.core.exceptions import MiddlewareNotUsed, ImproperlyConfigured
from django.db.models.loading import AppCache

from middleware import get_current_section, lookup_section_from_request
import settings as app_settings 

def section(request, section_path=None):
    return None

def asection(request, section_path=None):
    """
    A view of a section.
    """
    try:
        current_section = get_current_section()
    except MiddlewareNotUsed:
        current_section = lookup_section_from_request(request)
    section_url = current_section.get_absolute_url()
    extra = section_url.split(request.path)[-1]
    if extra == '':
        return simple.direct_to_template(request, 
            template = "scaffold/section.html",
            extra_context = {
                'node': current_section
            }
        )        
    else:
        if app_settings.FORWARD_TO:
            fwd_view = __import__(app_settings.FORWARD_TO)
            return fwd_view(request, slug=extra)
        app_cache = AppCache()
        try:
            app_cache.get('flatpages')
        except ImproperlyConfigured:
            raise Http404, "Section does not exist."
        
def bsection(request, section_path=None):
    # Normalize section path:
    if not section_path.startswith("/"):
        section_path = "/" + section_path
    if not section_path.endswith("/"):
        section_path = section_path + "/"
    current_section = get_current_section()
    if current_section:
        current_section_path = current_section.get_absolute_url()
        mount_point = app_settings.MOUNT_POINT
        if app_settings.MOUNT_POINT:
            mount_point = "/" + app_settings.MOUNT_POINT
            current_section_path = current_section_path.replace(
                mount_point, 
                "", 
                1
            )
        # The request is for a section page:
        if current_section_path == section_path:
            return simple.direct_to_template(request, 
                template = "scaffold/section.html",
                extra_context = {
                    'node': current_section
                }
            )
        # The request is (probably) for an article:
        if section_path.startswith(current_section_path):
            section_path = [s for s in section_path.split("/") if s != '']
            try:
                preview = section_path[-2] == 'preview'
            except IndexError:
                preview = False
            # Now forward the request on to the appropriate article view:
            slug = section_path[-1] 
            vw = preview and article_views.article_preview or article_views.article
            return vw(request, slug=slug)
        else:
            # All attempts to satisfy the request have failed.
            raise Http404, "Section or article does not exist."
    # If there is no section, the request may be for a flat page:
    else:

        try:
            return flatpage(request, request.path_info)
        except Http404:
            # All attempts to satisfy the request have failed.
            # Re-raise with an more accurate message:
            raise Http404, "URL does not exist."