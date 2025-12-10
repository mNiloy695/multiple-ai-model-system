
from django.shortcuts import render
from rest_framework import viewsets, permissions
from .serializers import RewardsHistorySerializer
from .models import RewardsHistory

class RewardsHistoryView(viewsets.ModelViewSet):
    queryset = RewardsHistory.objects.select_related('user').all().order_by('-created_at')
    serializer_class = RewardsHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_permission(self):
        if self.request.method in ['POST','GET']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return self.queryset.all()
        return self.queryset.filter(user=self.request.user)

    
            








