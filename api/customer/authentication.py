from rest_framework import authentication, exceptions
from django.utils import timezone
from .models import Customer, RevokedAuthToken
from django.core import signing
import hashlib

class CustomerTokenAuthentication(authentication.BaseAuthentication):
    """
    Custom authentication class for customer token authentication.
    """
    def authenticate(self, request):
        # Get the token from the Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '').split()
        
        if not auth_header or auth_header[0].lower() != 'bearer' or len(auth_header) != 2:
            return None

        token = auth_header[1]
        
        try:
            # Check if token is revoked
            fp = hashlib.sha256(token.encode("utf-8")).hexdigest()
            if RevokedAuthToken.objects.filter(fingerprint=fp, expires_at__gt=timezone.now()).exists():
                raise exceptions.AuthenticationFailed('Token has been revoked')

            # Verify and decode the token
            data = signing.loads(token, salt="customer-auth-token", max_age=60*60*24*7)  # 7 days
            
            # Get the customer
            try:
                customer = Customer.objects.get(pk=data.get("id"))
                return (customer, None)
            except Customer.DoesNotExist:
                raise exceptions.AuthenticationFailed('No such customer')
                
        except signing.SignatureExpired:
            raise exceptions.AuthenticationFailed('Token has expired')
        except signing.BadSignature:
            raise exceptions.AuthenticationFailed('Invalid token')
