from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser

from .models import Store
from .serializers import StoreSerializer


class StoreViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows stores to be viewed or edited.
    """
    queryset = Store.objects.all()
    serializer_class = StoreSerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'id'

    def get_queryset(self):
        """
        Optionally filter stores by city or state.
        """
        queryset = Store.objects.all()
        city = self.request.query_params.get('city', None)
        state = self.request.query_params.get('state', None)
        
        if city:
            queryset = queryset.filter(city__iexact=city)
        if state:
            queryset = queryset.filter(state__iexact=state)
            
        return queryset.order_by('store_name')

    @action(detail=False, methods=['get'])
    def locations(self, request):
        """
        Get a list of unique city and state combinations.
        """
        locations = Store.objects.values('city', 'state').distinct().order_by('state', 'city')
        return Response(locations)

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()
