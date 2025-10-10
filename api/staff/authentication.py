from rest_framework.authentication import TokenAuthentication as BaseTokenAuth
from rest_framework import exceptions
from .models import StaffToken

class StaffTokenAuthentication(BaseTokenAuth):
    """
    Simple token based authentication.
    Clients should authenticate by passing the token key in the "Authorization"
    HTTP header, prepended with the string "Token ".  For example:
        Authorization: Token 401f7ac837da42b97f613d789819ff93537bee6a
    """
    keyword = 'Token'
    model = StaffToken

    def authenticate_credentials(self, key):
        try:
            token = self.model.objects.get(key=key)
        except self.model.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid token')

        if not token.staff.is_active:
            raise exceptions.AuthenticationFailed('User inactive or deleted')
            
        if token.is_expired():
            raise exceptions.AuthenticationFailed('Token has expired')

        return (token.staff, token)
