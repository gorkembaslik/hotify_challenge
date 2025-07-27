from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.utils.translation import gettext as _
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

class LoginView(ObtainAuthToken):
    """Custom login endpoint that returns user info with token"""
    
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response({
                'error': _('Missing mandatory params')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(username=username, password=password)
        
        if user:
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user_id': user.pk,
                'username': user.username,
                'email': user.email
            })
        else:
            return Response({
                'error': _('Invalid credentials')
            }, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    """Logout endpoint that deletes the user's token"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            request.user.auth_token.delete()
            return Response({'message': _('Successfully logged out')})
        except:
            return Response({'error': _('Error logging out')}, status=status.HTTP_400_BAD_REQUEST)