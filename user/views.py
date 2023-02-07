import jwt
from .models import User
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response


class VerifyEmailView(APIView):
    def get(self, request):
        try:
            # import pdb; pdb.set_trace()
            token = request.GET.get("token")
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms="HS256")
            user = User.objects.get(id=payload["user_id"])

            if not user.is_verified:
                user.is_verified = True
                user.save()
            return Response({"message": "Successfully activated"})
        except jwt.ExpiredSignatureError as identifier:
            return Response({"error": "Activation Expired"})
        except jwt.exceptions.DecodeError as identifier:
            return Response({"error": "Invalid token"})

