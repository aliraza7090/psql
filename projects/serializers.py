from rest_framework import serializers
import json

from .models import Project


class ProjectSerializer(serializers.ModelSerializer):
    users = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Project
        fields = ('id', 'name', 'hubStaffId', 'avazaId', 'isActive', 'users')

    def get_users(self, obj):
        return json.loads(obj.users)


class UserProjectSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Project
        fields = ('id', 'name', 'hubStaffId', 'avazaId', 'isActive', 'user')

    def get_user(self, obj):
        email = self.context["email"]
        try:
            return [user for user in json.loads(obj.users) if user["email"] == email][0]
        except:
            return {}
