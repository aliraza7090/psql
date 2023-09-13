from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from ..serializers import UserSerializer

from ..utils.data_parser import remove_extra_spaces
from ..utils.user_helper import validate_password


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_profile(request):
    serializer = UserSerializer(request.user, many=False)
    return Response(serializer.data)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_profile(request):
    data = request.data
    data = remove_extra_spaces(data)

    data_keys = data.keys()

    user = request.user

    if 'designation' in data_keys:
        user.designation = data.get('designation')
    if 'name' in data_keys:
        user.first_name = data.get('name')
    if 'phone' in data_keys:
        user.phone = data.get('phone')
    if 'gender' in data_keys:
        user.gender = data.get('gender')
    if 'cnic' in data_keys:
        user.cnic = data.get('cnic')
    if 'dob' in data_keys:
        user.dob = data.get('dob')
    # if 'joinDate' in data_keys:
    #     user.joinDate = data.get('joinDate')
    if 'address' in data_keys:
        user.address = data.get('address')
    if 'skillSet' in data_keys:
        user.skillSet = data.get('skillSet')
    # Checking type to avoid null assignment
    # if type(data.get('isSupervisor')) == bool:
    #     user.isSupervisor = data.get('isSupervisor')
    # if type(data.get('isPartTime')) == bool:
    #     user.isPartTime = data.get('isPartTime')
    # if type(data.get('isIntern')) == bool:
    #     user.isIntern = data.get('isIntern')

    user.save()

    serializer = UserSerializer(user, many=False)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def change_password(request):
    data = request.data
    data = remove_extra_spaces(data)
    user = request.user

    new_password = data.get('newPassword')
    old_password = data.get('oldPassword')

    if not new_password or not old_password:
        message = {"detail": "Please provide both (old and new) password"}
        return Response(message, status=status.HTTP_400_BAD_REQUEST)

    if not user.check_password(data.get("oldPassword")):
        message = {"detail": "Old password is incorrect"}
        return Response(message, status=status.HTTP_400_BAD_REQUEST)

    is_password_valid, password_message = validate_password(new_password)
    if not is_password_valid:
        message = {"detail": password_message}
        return Response(message, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save()

    message = {"detail": "Password changed successfully"}
    return Response(message, status=status.HTTP_200_OK)
