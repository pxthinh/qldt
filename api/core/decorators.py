import logging
from functools import wraps
from django.http import JsonResponse
from rest_framework.authentication import get_authorization_header
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)
User = get_user_model()

# Import your custom token model
try:
    from api.staff.models import StaffToken
except ImportError:
    try:
        from staff.models import StaffToken
    except ImportError:
        logger.error("Failed to import StaffToken model. Make sure it's in the staff app.")
        raise


def get_token_from_request(request):
    """Extract token from request headers"""
    auth = get_authorization_header(request).split()
    if not auth or auth[0].lower() != b'bearer':
        return None
    if len(auth) == 1:
        return None
    elif len(auth) > 2:
        return None
    return auth[1].decode('utf-8')


def staff_required(require_manager=False):
    """
    Decorator that ensures the user is authenticated and is a staff member.
    If require_manager is True, enforces manager-level access for staff management.
    Uses custom StaffToken model for authentication.

    Args:
        require_manager (bool): If True, enforces manager-level access for staff management.
                                If False, allows any staff member to access the view.
    """

    def decorator(view_func):
        # Make the view CSRF exempt using Django's built-in decorator
        view_func = csrf_exempt(view_func)

        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Get token from request
            token_key = get_token_from_request(request)
            if not token_key:
                return JsonResponse(
                    {"detail": "No valid token provided. Use 'Bearer <token>' format."},
                    status=403
                )

            try:
                # Get token from database using custom StaffToken model
                try:
                    token = StaffToken.objects.select_related('staff').get(key=token_key)
                except StaffToken.DoesNotExist:
                    logger.warning(f"Staff token not found: {token_key}")
                    return JsonResponse(
                        {"detail": "Invalid or expired token."},
                        status=403
                    )

                # Check if token is expired
                if token.is_expired():
                    logger.warning(f"Token expired: {token_key}")
                    token.delete()
                    return JsonResponse(
                        {"detail": "Token has expired. Please log in again."},
                        status=403
                    )

                # Set user from token's staff
                request.user = token.staff
                request.auth = token

                logger.info(f"Authenticated staff: {request.user.username}")

                # Check if staff is active
                if not request.user.is_active:
                    return JsonResponse(
                        {"detail": "Staff account is disabled."},
                        status=403
                    )

                # Check if this is a staff management endpoint
                is_staff_management = any(
                    path in request.path
                    for path in ['/api/admin/staff/', '/staff/']
                )

                # If this is a staff management endpoint and manager is required
                if is_staff_management and require_manager:
                    # A manager is either:
                    # 1. A staff with no manager (manager_id is null), or
                    # 2. A staff who has subordinates
                    is_manager = (
                            request.user.manager_id is None or  # No manager (top-level)
                            (hasattr(request.user, 'subordinates') and request.user.subordinates.exists())
                    # Has subordinates
                    )
                    if not is_manager:
                        return JsonResponse(
                            {"detail": "Manager privileges required to manage staff accounts."},
                            status=403
                        )

                return view_func(request, *args, **kwargs)

            except Exception as e:
                logger.error(f"Authentication error: {str(e)}", exc_info=True)
                return JsonResponse(
                    {"detail": "Authentication failed. Please log in again."},
                    status=403
                )

        return _wrapped_view

    return decorator
