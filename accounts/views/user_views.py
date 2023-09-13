from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework import status
from django.contrib.auth.hashers import make_password
from django.db import transaction

from leaves.utils.leave_helper import calculate_leaves
from leaves.models import LeaveStatistic

from ..models import User
from ..serializers import UserSerializer

from ..utils.data_parser import remove_extra_spaces
from ..utils.user_helper import (
    generate_random_password,
    is_email_valid,
    send_email_custom,
    validate_password,
)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_users(request):
    email = request.GET.get("email")
    users = None
    request_user = request.user
    if request_user.isSupervisor or request_user.is_staff:
        if email:
            if request_user.is_staff:
                # There'll be only one user against an email address, so no need to use get or first.
                users = User.objects.filter(email=email)
            elif request_user.isSupervisor:
                filtered_user = User.objects.filter(email=email)
                if filtered_user and request_user.is_supervisor_of(
                    filtered_user.first()
                ):
                    users = filtered_user
        else:
            if request_user.is_staff:
                users = User.objects.all()
            elif request_user.isSupervisor:
                users = User.objects.filter(supervisors__id=request_user.id)
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
    else:
        message = {"detail": "You do not have permission to perform this action"}
        return Response(message, status=status.HTTP_403_FORBIDDEN)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def get_user_by_id(request, id):
    try:
        user = User.objects.get(id=id)
        serializer = UserSerializer(user, many=False)
        return Response(serializer.data)
    except User.DoesNotExist:
        message = {"detail": "User not found."}
        return Response(message, status=status.HTTP_404_NOT_FOUND)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def delete_user(request):
    user = request.user
    data = request.data

    if not user.check_password(data.get("password")):
        message = {"detail": "Password is incorrect"}
        return Response(message, status=status.HTTP_403_FORBIDDEN)

    user_to_delete = None

    try:
        user_to_delete = User.objects.get(id=data.get("id"))
    except User.DoesNotExist:
        message = {"detail": "User does not exist"}
        return Response(message, status=status.HTTP_404_NOT_FOUND)

    user_to_delete.delete()

    message = {"detail": "User has been deleted"}
    return Response(message, status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def create_user(request):
    # Get the model field names that don't have default values
    data = request.data
    data_keys = data.keys()
    frontend_url = request.META.get("HTTP_REFERER")

    required_fields = [
        "email",
        "designation",
    ]

    # Check if all required fields are present in the request data
    if all(field in data_keys for field in required_fields):
        data = remove_extra_spaces(data)

        if not is_email_valid(data.get("email")):
            message = {"detail": f"Please provide a valid email address"}
            return Response(message, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=data.get("email")).exists():
            message = {"detail": f"User with provided email already exists"}
            return Response(message, status=status.HTTP_400_BAD_REQUEST)

        # '' and False for fields which are not present in the data
        email = request.data.get("email").lower()
        designation = request.data.get("designation")
        name = request.data.get("name", "")
        phone = request.data.get("phone", "")
        gender = request.data.get("gender", "")
        cnic = request.data.get("cnic", "")
        # datefield doesn't accept ''. null is allowed
        dob = request.data.get("dob")
        joinDate = request.data.get("joinDate")
        address = request.data.get("address", "")
        skillSet = request.data.get("skillSet", "")
        isSupervisor = request.data.get("isSupervisor", False)
        jobType = request.data.get("jobType", "")
        password = generate_random_password()

        try:
            # The transaction.atomic() context manager ensures that the entire transaction is atomic and will be rolled back if an exception occurs.
            with transaction.atomic():
                user = User.objects.create(
                    username=email,
                    email=email,
                    password=make_password(password),
                    designation=designation,
                    first_name=name,
                    phone=phone,
                    gender=gender,
                    cnic=cnic,
                    dob=dob,
                    joinDate=joinDate,
                    address=address,
                    skillSet=skillSet,
                    isSupervisor=isSupervisor,
                    jobType=jobType,
                )

                leave_stats = calculate_leaves(joinDate, jobType, isAnnualAllowed=False)

                LeaveStatistic.objects.create(
                    user=user,
                    annualAllowed=leave_stats.get("annualAllowed"),
                    casualAllowed=leave_stats.get("casualAllowed"),
                    sickAllowed=leave_stats.get("sickAllowed"),
                )

                send_email_custom(
                    "Invitation",
                    f"Please use following credentials to login to {frontend_url}. \n\n email: {email} \n password: {password}",
                    [email],
                )

                supervisors = request.data.get(
                    "supervisors"
                )  # list of supervisors (should contain IDs)
                if supervisors:
                    supervisors_to_add = User.objects.filter(id__in=supervisors)
                    user.supervisors.add(*supervisors_to_add)

                serializer = UserSerializer(user, many=False)

                return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            message = {
                "detail": "Error occurred. Please make sure you are providing valid information"
            }
            return Response(message, status=status.HTTP_400_BAD_REQUEST)
    else:
        message = {
            "detail": f"Please provide required fields i.e., {', '.join(required_fields)}"
        }
        return Response(message, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PATCH"])
@permission_classes([IsAdminUser])
def edit_user(request, id):
    data = request.data
    data = remove_extra_spaces(data)

    data_keys = data.keys()  # To check if fields are present in data
    existing_joinDate = None  # To check if new join date is different from existing

    try:
        user = User.objects.get(id=id)

        if type(data.get("isActive")) == bool:
            user.is_active = data.get("isActive")

        # if "designation" in data_keys:
        #     user.designation = data.get("designation")
        if "name" in data_keys:
            user.first_name = data.get("name")
        if "phone" in data_keys:
            user.phone = data.get("phone")
        if "gender" in data_keys:
            user.gender = data.get("gender")
        if "cnic" in data_keys:
            user.cnic = data.get("cnic")
        if "dob" in data_keys:
            user.dob = data.get("dob")
        if "joinDate" in data_keys:
            existing_joinDate = user.joinDate
            user.joinDate = data.get("joinDate")
        if "address" in data_keys:
            user.address = data.get("address")
        if "designation" in data_keys:
            user.designation = data.get("designation")
        if "skillSet" in data_keys:
            user.skillSet = data.get("skillSet")
        if "jobType" in data_keys:
            user.jobType = data.get("jobType")
        # Checking type to avoid null assignment
        if type(data.get("isSupervisor")) == bool:
            user.isSupervisor = data.get("isSupervisor")
        if type(data.get("isPartTime")) == bool:
            user.isPartTime = data.get("isPartTime")
        if type(data.get("isIntern")) == bool:
            user.isIntern = data.get("isIntern")

        supervisors = request.data.get(
            "supervisors"
        )  # list of supervisors (should contain IDs)

        if type(supervisors) == list:
            if supervisors:  # If supervisors list contains any value
                new_supervisors = set(
                    User.objects.filter(id__in=supervisors)
                )  # Converting to set so can perform calculations
                existing_supervisors = set(user.supervisors.all())

                # add/remove if new is different from existing
                if new_supervisors != existing_supervisors:
                    # Remove any supervisors that are not in the new set
                    for supervisor in existing_supervisors - new_supervisors:
                        user.supervisors.remove(supervisor)

                    # Add any new supervisors that are not already in the existing set
                    for supervisor in new_supervisors - existing_supervisors:
                        if supervisor not in existing_supervisors:
                            user.supervisors.add(supervisor)
            else:  # No Supervisor
                # We need to run save() after clear() to persist the changes to the database.
                user.supervisors.clear()

        if not user.isSupervisor or not user.is_active:
            supervision_users = User.objects.filter(supervisors__id=user.id)
            for supervision_user in supervision_users:
                # We don't need to perform an update query in this case, as the modification is done directly on the related user instances.
                # We don't need to run save() after remove() to persist the changes to the database.
                supervision_user.supervisors.remove(user)

        user.save()

        # Update user leaves if joining date is changed
        if data.get("joinDate") and data.get("joinDate") != existing_joinDate:
            leave_stats = calculate_leaves(
                user.joinDate, user.jobType, isAnnualAllowed=user.isAnnualAllowed
            )
            LeaveStatistic.objects.filter(user=user).update(
                annualAllowed=leave_stats.get("annualAllowed"),
                casualAllowed=leave_stats.get("casualAllowed"),
                sickAllowed=leave_stats.get("sickAllowed"),
            )

        serializer = UserSerializer(user, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        message = {"detail": "User does not exist"}
        return Response(message, status=status.HTTP_404_NOT_FOUND)
