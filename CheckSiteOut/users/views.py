from datetime import timedelta
from django.contrib.auth import get_user_model
from django.shortcuts import render
from rest_framework.views import APIView, Response
import secrets
from .models import Token
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
User = get_user_model()

class GetTokenApiView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        token = Token.objects.create(token=secrets.token_urlsafe(32))
        return Response({
            'token': token.token,
            'bot_link': f'https://t.me/CheckSiteOut_bot?start={ token.token }',
        })


class PollTokenApiView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        token = request.query_params.get('token')

        login_token = Token.objects.filter(
            token=token, created_at__gte=timezone.now() - timedelta(hours=1)
        ).first()
        if login_token is None:
            return Response({'status': 'invalid'}, status=404)
        if login_token.telegram_id is None:
            return Response({'status': 'pending'})
        user, _ = User.objects.get_or_create(
            username=f'tg_{login_token.telegram_id}'
        )
        login_token.delete()
        refresh = RefreshToken.for_user(user)
        return Response({
            'status': 'ok',
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        })