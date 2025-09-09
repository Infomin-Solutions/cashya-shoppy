"""
Custom middleware for CSRF handling with wildcard support
"""
import re
from django.middleware.csrf import CsrfViewMiddleware
from django.conf import settings
from django.utils.cache import patch_vary_headers
from urllib.parse import urlparse


class WildcardCsrfViewMiddleware(CsrfViewMiddleware):
    """
    Custom CSRF middleware that supports wildcard entries in CSRF_TRUSTED_ORIGINS
    """

    def _is_trusted_origin(self, origin):
        """
        Check if an origin is trusted, supporting wildcard patterns
        """
        if not origin:
            return False

        # Get the CSRF trusted origins from settings
        trusted_origins = getattr(settings, 'CSRF_TRUSTED_ORIGINS', [])

        # If '*' is in trusted origins, allow all
        if '*' in trusted_origins:
            return True

        # Parse the origin URL
        parsed_origin = urlparse(origin)
        origin_scheme_host = f"{parsed_origin.scheme}://{parsed_origin.netloc}"

        for trusted in trusted_origins:
            # Handle exact matches
            if trusted == origin_scheme_host:
                return True

            # Handle wildcard patterns
            if '*' in trusted:
                # Convert wildcard pattern to regex
                # Escape special regex characters except *
                pattern = re.escape(trusted).replace(r'\*', '.*')
                if re.match(f"^{pattern}$", origin_scheme_host):
                    return True

        return False

    def process_view(self, request, callback, callback_args, callback_kwargs):
        """
        Override the process_view method to use our custom origin checking
        """
        if getattr(request, 'csrf_processing_done', False):
            return None

        # Check if CSRF is disabled for this view
        if getattr(callback, 'csrf_exempt', False):
            return None

        # For non-safe methods, check CSRF
        if request.method not in ('GET', 'HEAD', 'OPTIONS', 'TRACE'):
            # Check referer
            referer = request.META.get('HTTP_REFERER')
            if referer is not None:
                if not self._is_trusted_origin(referer):
                    # Check if it's a same-origin request
                    good_hosts = self._get_good_hosts(request)
                    parsed_referer = urlparse(referer)
                    if parsed_referer.netloc not in good_hosts:
                        return self._reject(request, "Referer checking failed - origin not trusted.")

        # Continue with normal CSRF processing
        return super().process_view(request, callback, callback_args, callback_kwargs)

    def _get_good_hosts(self, request):
        """
        Get the list of allowed hosts
        """
        allowed_hosts = settings.ALLOWED_HOSTS
        if settings.DEBUG and not allowed_hosts:
            allowed_hosts = ['localhost', '127.0.0.1', '[::1]']

        good_hosts = set()
        for host in allowed_hosts:
            if host == '*':
                # If ALLOWED_HOSTS contains '*', we trust the Host header
                return {request.get_host()}
            else:
                good_hosts.add(host)

        return good_hosts
