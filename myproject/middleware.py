"""
Custom middleware for CSRF handling with wildcard support
"""
import re
import logging
from django.middleware.csrf import CsrfViewMiddleware
from django.conf import settings
from django.utils.cache import patch_vary_headers
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


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

                # First try matching with the full origin (scheme://host:port or scheme://host)
                if re.match(f"^{pattern}$", origin_scheme_host):
                    return True

                # Also try matching with default ports added
                # HTTPS default port 443, HTTP default port 80
                if parsed_origin.scheme == 'https' and ':' not in parsed_origin.netloc:
                    origin_with_port = f"{origin_scheme_host}:443"
                    if re.match(f"^{pattern}$", origin_with_port):
                        return True
                elif parsed_origin.scheme == 'http' and ':' not in parsed_origin.netloc:
                    origin_with_port = f"{origin_scheme_host}:80"
                    if re.match(f"^{pattern}$", origin_with_port):
                        return True

        return False

    def _check_referer(self, request):
        """
        Check if the referer is trusted using our custom wildcard logic
        Returns True if referer is trusted, False if not trusted or missing
        """
        referer = request.META.get('HTTP_REFERER')
        if referer is None:
            return False

        is_trusted = self._is_trusted_origin(referer)
        if settings.DEBUG:
            logger.debug(
                f"Referer check: {referer} -> {'TRUSTED' if is_trusted else 'REJECTED'}")
        return is_trusted

    def _check_origin(self, request):
        """
        Check if the origin is trusted using our custom wildcard logic
        """
        origin = request.META.get('HTTP_ORIGIN')
        if origin is None:
            return False

        is_trusted = self._is_trusted_origin(origin)
        if settings.DEBUG:
            logger.debug(
                f"Origin check: {origin} -> {'TRUSTED' if is_trusted else 'REJECTED'}")
        return is_trusted

    def _reject(self, request, reason):
        """
        Override to provide better error messages
        """
        return super()._reject(request, reason)

    def process_view(self, request, callback, callback_args, callback_kwargs):
        """
        Complete CSRF processing with custom wildcard origin checking
        """
        if getattr(request, "csrf_processing_done", False):
            return None

        # Wait until request.META["CSRF_COOKIE"] has been manipulated before
        # bailing out, so that get_token still works
        if getattr(callback, "csrf_exempt", False):
            return None

        # Assume that anything not defined as 'safe' by RFC 9110 needs protection
        if request.method in ("GET", "HEAD", "OPTIONS", "TRACE"):
            return self._accept(request)

        if getattr(request, "_dont_enforce_csrf_checks", False):
            # Mechanism to turn off CSRF checks for test suite. It comes after
            # the creation of CSRF cookies, so that everything else continues
            # to work exactly the same (e.g. cookies are sent, etc.), but
            # before any branches that call the _reject method.
            return self._accept(request)

        # Reject the request if the Origin header doesn't match an allowed
        # value using our custom wildcard logic.
        if "HTTP_ORIGIN" in request.META:
            if not self._check_origin(request):
                origin = request.META["HTTP_ORIGIN"]
                return self._reject(request, f"Origin checking failed - {origin} does not match any trusted origins.")
        elif request.is_secure():
            # If the Origin header wasn't provided, reject HTTPS requests if
            # the Referer header doesn't match an allowed value using our custom logic.
            if not self._check_referer(request):
                referer = request.META.get('HTTP_REFERER', 'None')
                return self._reject(request, f"Referer checking failed - {referer} does not match any trusted origins.")

        # Check CSRF token
        try:
            self._check_token(request)
        except Exception as exc:
            return self._reject(request, str(exc))

        return self._accept(request)
