from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken

from ..serializers import MyTokenObtainPairSerializer, UserSerializerWithToken
from ..models import User

from ..utils.user_helper import send_email_custom, validate_password


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


@api_view(["POST"])
def forget_password(request):
    data = request.data
    user_email = data.get("email")
    client_url = request.META.get("HTTP_REFERER")
    reset_password_url = f"{client_url}reset-password"

    try:
        user = User.objects.get(email__iexact=user_email)
        print(user)
        serializer = UserSerializerWithToken(user, many=False)
        token = serializer.data.get("token")

        send_email_custom(
            "Password Reset Link", "/".join([reset_password_url, token]), [user_email]
        )
        message = {"detail": f"Password reset link has been sent to {user_email}"}
        return Response(message, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        message = {"detail": "There is no any account associated with this email."}
        return Response(message, status=status.HTTP_404_NOT_FOUND)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def reset_password(request):
    data = request.data
    password = data.get("password")

    try:
        if not password:
            message = {"detail": "Password not provided"}
            return Response(message, status=status.HTTP_400_BAD_REQUEST)

        is_password_valid, password_validity_message = validate_password(password)
        if not is_password_valid:
            message = {"detail": password_validity_message}
            return Response(message, status=status.HTTP_400_BAD_REQUEST)

        request.user.set_password(password)
        request.user.save()

        message = {"detail": "Password reset successfully"}
        return Response(message, status=status.HTTP_200_OK)

    except Exception as e:
        message = {"detail": "Password reset link is invalid or expired"}
        return Response(message, status=status.HTTP_401_UNAUTHORIZED)
