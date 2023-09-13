from rest_framework import serializers

from .models import Leave, LeaveStatistic


class LeaveSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)
    updatedBy = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Leave
        fields = (
            "id",
            "user",
            "description",
            "startDate",
            "endDate",
            "days",
            "status",
            "leaveType",
            "isHalf",
            "updatedBy",
            "updatedAt",
            "createdAt",
        )

    def get_user(self, obj):
        return {
            "id": obj.user.id,
            "name": obj.user.first_name,
            "email": obj.user.email,
            "designation": obj.user.designation,
        }

    def get_updatedBy(self, obj):
        res_dict = (
            {
                "id": obj.updatedBy.id,
                "name": obj.updatedBy.first_name,
                "email": obj.updatedBy.email,
                "designation": obj.user.designation,
            }
            if obj.updatedBy
            else None
        )

        return res_dict


class LeaveStatisticSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveStatistic
        fields = (
            "annualAllowed",
            "annualUtilized",
            "casualAllowed",
            "casualUtilized",
            "sickAllowed",
            "sickUtilized",
            "unpaidUtilized",
        )
