
# import logging
# import re
# import html

# from django.conf import settings
# from django.http import JsonResponse, Http404
# from django.core.exceptions import PermissionDenied, SuspiciousOperation
# from django.utils.html import strip_tags

# logger = logging.getLogger(__name__)


# class JsonErrorMiddleware:

#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         response = self.get_response(request)

#         # JSON requested ആണെങ്കിൽ മാത്രം error response JSON ആക്കുക
#         if "application/json" not in request.headers.get("Accept", ""):
#             return response

#         # Success response മാറ്റരുത്
#         if response.status_code < 400:
#             return response

#         # Already JSON response ആണെങ്കിൽ മാറ്റരുത്
#         if "application/json" in response.get("Content-Type", ""):
#             return response

#         status_code = response.status_code

#         error_names = {
#             400: "BadRequest",
#             403: "PermissionDenied",
#             404: "Http404",
#             500: "InternalServerError",
#         }

#         error_name = error_names.get(status_code, "HTTPError")

#         # Original HTML error response-ൽ നിന്ന് message എടുക്കുക
#         message = ""

#         if not getattr(response, "streaming", False):
#             try:
#                 content = response.content.decode(
#                     response.charset or "utf-8",
#                     errors="replace"
#                 )
#                 message = strip_tags(content)
#                 message = html.unescape(message)
#                 message = re.sub(r"\s+", " ", message).strip()
#                 message = message[:500]
#             except Exception:
#                 message = ""

#         if not message:
#             message = response.reason_phrase or "Request failed."

#         logger.warning(
#             "HTTP error response: status=%s path=%s",
#             status_code,
#             request.path
#         )

#         return JsonResponse(
#             {
#                 "success": False,
#                 "status": status_code,
#                 "error": error_name,
#                 "message": message,
#             },
#             status=status_code,
#         )


#     def process_exception(self, request, exception):

#         if "application/json" not in request.headers.get("Accept", ""):
#             return None

#         if isinstance(exception, Http404):
#             status_code = 404
#         elif isinstance(exception, PermissionDenied):
#             status_code = 403
#         elif isinstance(exception, SuspiciousOperation):
#             status_code = 400
#         else:
#             status_code = 500

#         logger.exception("Request error: %s", exception)

#         if settings.DEBUG:
#             message = str(exception) or exception.__class__.__name__
#         else:
#             message = "Something went wrong. Please try again later."

#         return JsonResponse(
#             {
#                 "success": False,
#                 "status": status_code,
#                 "error": exception.__class__.__name__,
#                 "message": message,
#             },
#             status=status_code,
#         )





import logging
import re
import html

from django.conf import settings
from django.http import JsonResponse, Http404
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


class JsonErrorMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Only handle requests asking for JSON
        if "application/json" not in request.headers.get("Accept", ""):
            return response

        # Do not change successful responses
        if response.status_code < 400:
            return response

        # Do not change responses already in JSON format
        if "application/json" in response.get("Content-Type", ""):
            return response

        status_code = response.status_code

        error_names = {
            400: "BadRequest",
            401: "Unauthorized",
            403: "PermissionDenied",
            404: "Http404",
            405: "MethodNotAllowed",
            409: "Conflict",
            429: "TooManyRequests",
            500: "InternalServerError",
        }

        error_name = error_names.get(status_code, "HTTPError")

        message = ""

        # Extract a short message from non-streaming HTML responses
        if not getattr(response, "streaming", False):
            try:
                content = response.content.decode(
                    response.charset or "utf-8",
                    errors="replace"
                )

                # Prefer the page heading or title over the full HTML
                heading = re.search(
                    r"<h1[^>]*>(.*?)</h1>",
                    content,
                    re.IGNORECASE | re.DOTALL
                )

                title = re.search(
                    r"<title[^>]*>(.*?)</title>",
                    content,
                    re.IGNORECASE | re.DOTALL
                )

                if heading:
                    message = heading.group(1)
                elif title:
                    message = title.group(1)

                message = html.unescape(strip_tags(message))
                message = re.sub(r"\s+", " ", message).strip()

            except Exception:
                logger.exception("Could not extract error response message")

        if not message:
            message = response.reason_phrase or "Request failed."

        logger.warning(
            "HTTP error response: status=%s path=%s",
            status_code,
            request.path
        )

        return JsonResponse(
            {
                "success": False,
                "status": status_code,
                "error": error_name,
                "message": message,
            },
            status=status_code,
        )

    def process_exception(self, request, exception):

        if "application/json" not in request.headers.get("Accept", ""):
            return None

        if isinstance(exception, Http404):
            status_code = 404
        elif isinstance(exception, PermissionDenied):
            status_code = 403
        elif isinstance(exception, SuspiciousOperation):
            status_code = 400
        else:
            status_code = 500

        logger.exception("Request error: %s", exception)

        if settings.DEBUG:
            message = str(exception) or exception.__class__.__name__
        else:
            message = "Something went wrong. Please try again later."

        return JsonResponse(
            {
                "success": False,
                "status": status_code,
                "error": exception.__class__.__name__,
                "message": message,
            },
            status=status_code,
        )
