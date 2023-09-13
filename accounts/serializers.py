from rest_framework import exceptions, serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.settings import api_settings
from django.contrib.auth.models import update_last_login
from django.contrib.auth import authenticate
import re

from leaves.models import LeaveStatistic
from leaves.serializers import LeaveStatisticSerializer

from .models import User


class UserSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField(read_only=True)  # To use get_name
    isAdmin = serializers.SerializerMethodField(
        read_only=True)  # To use get_isAdmin
    isActive = serializers.SerializerMethodField(
        read_only=True)  # To use get_isActive
    supervisors = serializers.SerializerMethodField(read_only=True)
    leaveStatistics = serializers.SerializerMethodField(read_only=True)
    skillSet = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User

        fields = [
            "id",
            "username",
            "email",
            "name",
            "phone",
            "cnic",
            "gender",
            "dob",
            "joinDate",
            "address",
            "designation",
            "skillSet",
            "jobType",
            "isActive",
            "isAdmin",
            "isSupervisor",
            "isAccountSetup",
            "supervisors",
            "leaveStatistics",
            "hubStaffPresence",
            "avazaPresence",
            "hubStaffId",
            "avazaId",
            "createdAt",
        ]

    def get_name(self, obj):
        name = obj.first_name
        if name == "":
            name = obj.email
        return name

    def get_isAdmin(self, obj):
        return obj.is_staff

    def get_isActive(self, obj):
        return obj.is_active

    def get_supervisors(self, obj):
        supervisors = [
            {
                "value": supervisor.id,
                "label": f"{supervisor.first_name} - ({supervisor.designation})",
            }
            for supervisor in obj.supervisors.all()
        ]
        return supervisors

    def get_leaveStatistics(self, obj):
        leave_stat = LeaveStatistic.objects.filter(user=obj).first()
        return (
            LeaveStatisticSerializer(
                leave_stat, many=False).data if leave_stat else {}
        )

    def get_skillSet(self, obj):
        skills = [
            {"value": skill, "label": skill}
            for skill in re.split(
                ",\s|,", obj.skillSet
            )  # we have skillSet in string, splitting it using "," and ", ". And than formatting for frontend
        ] if len(obj.skillSet) > 0 else []
        return skills


class UserSerializerWithToken(UserSerializer):
    token = serializers.SerializerMethodField(read_only=True)
    refresh = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User

        fields = [
            "id",
            "username",
            "email",
            "name",
            "phone",
            "cnic",
            "gender",
            "dob",
            "joinDate",
            "address",
            "designation",
            "skillSet",
            "jobType",
            "isActive",
            "isAdmin",
            "isSupervisor",
            "isAccountSetup",
            "supervisors",
            "leaveStatistics",
            "hubStaffPresence",
            "avazaPresence",
            "hubStaffId",
            "avazaId",
            "createdAt",
            "token",
            "refresh",
        ]

    def get_token(self, obj):
        token = RefreshToken.for_user(obj)
        return str(token.access_token)

    def get_refresh(self, obj):
        token = RefreshToken.for_user(obj)
        return str(token)


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    # def validate(self, attrs):
    # data = super().validate(attrs)
    def validate(self, attrs):
        # remove the case check by converting the username to lowercase
        username = attrs.get(self.username_field).lower()
        password = attrs.get("password")

        user = User.objects.filter(username=username).first()
        if user.check_password(password) and not user.is_active:
            raise exceptions.AuthenticationFailed(
                "Your account is inactive, Please contact your administration."
            )

        user = authenticate(
            request=self.context.get("request"), username=username, password=password
        )
        if not user:
            raise exceptions.AuthenticationFailed(
                "Unable to login with provided credentials."
            )

        if api_settings.UPDATE_LAST_LOGIN:
            update_last_login(None, user)

        serializer = UserSerializerWithToken(user).data

        return serializer
