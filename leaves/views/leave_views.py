from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework import status
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q
from django.db.models import Sum

from accounts.utils.data_parser import remove_extra_spaces
from accounts.utils.user_helper import send_email_custom
from accounts.models import User

from ..serializers import LeaveSerializer, LeaveStatisticSerializer
from ..models import Leave, LeaveStatistic
from ..utils.leave_helper import send_update_leave_notification_email


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_leave(request):
    user = request.user
    data = request.data
    frontend_url = request.META.get("HTTP_REFERER")
    data_keys = data.keys()

    required_fields = ["startDate", "endDate", "leaveType"]

    # Check if all required fields are present in the request data
    if all(field in data_keys for field in required_fields):
        data = remove_extra_spaces(data)

        description = data.get("description", "")
        startDate = data.get("startDate")
        endDate = data.get("endDate")
        leaveType = data.get("leaveType")
        isHalf = data.get("isHalf", False)

        # convert the date strings to datetime objects
        start_dt = datetime.strptime(startDate, "%Y-%m-%d")
        end_dt = datetime.strptime(endDate, "%Y-%m-%d")

        # calculate the number of days between the two dates
        # add 1 to include both start and end dates
        num_days = (end_dt - start_dt).days + 1

        if num_days < 1:
            message = {"detail": "The end date cannot be before the start date"}
            return Response(message, status=status.HTTP_400_BAD_REQUEST)

        # Check if user has already created a leave request for a date between start and end
        overlap_leaves = Leave.objects.filter(
            Q(user=user)
            & (
                (
                    Q(startDate__gte=startDate) & Q(startDate__lte=endDate)
                )  #  It will check if any of existing request's startDate is between new request's startDate and endDate
                | (
                    Q(endDate__gte=startDate) & Q(endDate__lte=endDate)
                )  #  It will check if any of existing request's endDate is between new request's startDate and endDate
            )
        ).exclude(Q(status="withdrawn") | Q(status="declined"))

        if overlap_leaves.exists():
            message = {
                "detail": f"""Leave request already exists i.e., {', '.join([str(leave.startDate) if leave.days == 1 
                    else f'{str(leave.startDate)} to {str(leave.endDate)}' for leave in overlap_leaves])}"""
            }
            return Response(message, status=status.HTTP_400_BAD_REQUEST)

        # count the number of weekdays
        weekdays = 0
        for i in range(num_days):
            date = start_dt + timedelta(days=i)
            if (
                date.weekday() < 5
            ):  # weekday() returns 0 for Monday, 1 for Tuesday, ..., 6 for Sunday
                weekdays += 1

        if isHalf:
            weekdays = weekdays / 2

        leave_stat = LeaveStatistic.objects.get(user=user)

        pending_leave_days = Leave.objects.filter(
            user=user, leaveType=leaveType, status="pending"
        ).aggregate(total_days=Sum("days"))["total_days"]

        if (
            (
                leaveType == "casual"
                and (
                    leave_stat.casualUtilized + weekdays > leave_stat.casualAllowed
                    or pending_leave_days + weekdays > leave_stat.casualAllowed
                )
            )
            or (
                leaveType == "sick"
                and (
                    leave_stat.sickUtilized + weekdays > leave_stat.sickAllowed
                    or pending_leave_days + weekdays > leave_stat.sickAllowed
                )
            )
            or (
                leaveType == "annual"
                and (
                    leave_stat.annualUtilized + weekdays > leave_stat.annualAllowed
                    or pending_leave_days + weekdays > leave_stat.annualAllowed
                )
            )
        ):
            message = {
                "detail": "Leave limit exceeded. Please try to withdraw pending leave requests"
            }
            return Response(message, status=status.HTTP_400_BAD_REQUEST)

        new_leave = Leave.objects.create(
            user=user,
            description=description,
            startDate=startDate,
            endDate=endDate,
            leaveType=leaveType,
            isHalf=isHalf,
            days=weekdays,
        )

        supervisor_emails = [supervisor.email for supervisor in user.supervisors.all()]

        email_message = f"""{user.get_title()} has generated {leaveType} leave request for {
                        startDate if startDate == endDate 
                            else startDate + " to " + endDate
                        } ({weekdays} day). Please visit {frontend_url}req_listing/{new_leave.id} for more details."""

        send_email_custom(
            subject=f"Leave Request by {user.get_title()}",
            body=email_message,
            recipients=supervisor_emails,
        )
        # print(email_message)

        serializer = LeaveSerializer(new_leave, many=False)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    else:
        message = {
            "detail": f"Please provide all required fields i.e., {', '.join(required_fields)}"
        }
        return Response(message, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_leave(request, id):
    user = request.user
    data = request.data
    frontend_url = request.META.get("HTTP_REFERER")
    data_keys = data.keys()

    required_fields = [
        "status",
    ]

    if all(field in data_keys for field in required_fields):
        data = remove_extra_spaces(data)
        leave_status = data.get("status", "")

        try:
            leave = Leave.objects.get(id=id)
        except Leave.DoesNotExist:
            message = {"detail": "Leave request does not exists"}
            return Response(message, status=status.HTTP_404_NOT_FOUND)

        if leave_status.lower() == "declined" or leave_status.lower() == "approved":
            if (
                user.is_staff
                or user.isSupervisor
                and (
                    user.id
                    in [supervisor.id for supervisor in leave.user.supervisors.all()]
                )
            ):
                leave.status = leave_status

                if leave_status.lower() == "approved":
                    leave_stat = LeaveStatistic.objects.get(user=leave.user)
                    if leave.leaveType == "casual":
                        leave_stat.casualUtilized = (
                            leave_stat.casualUtilized + leave.days
                        )
                    elif leave.leaveType == "sick":
                        leave_stat.sickUtilized = leave_stat.sickUtilized + leave.days
                    elif leave.leaveType == "annual":
                        leave_stat.annualUtilized = (
                            leave_stat.annualUtilized + leave.days
                        )
                    elif leave.leaveType == "unpaid":
                        leave_stat.unpaidUtilized = (
                            leave_stat.unpaidUtilized + leave.days
                        )

                    leave_stat.save()

            else:
                message = {
                    "detail": "You do not have permission to perform this action"
                }
                return Response(message, status=status.HTTP_403_FORBIDDEN)
        elif leave_status.lower() == "withdrawn":
            leave.status = leave_status
        else:
            message = {"detail": "Invalid value provided for leave status"}
            return Response(message, status=status.HTTP_400_BAD_REQUEST)

        leave.updated_by = user
        leave.updated_at = timezone.now()
        leave.save()

        send_update_leave_notification_email(leave, user, frontend_url)

        serializer = LeaveSerializer(leave, many=False)
        return Response(serializer.data)

    else:
        message = {
            "detail": f"Please provide required fields i.e., {', '.join(required_fields)}"
        }
        return Response(message, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_leaves(request):
    user = request.user

    # Sent Leave Requests | pending first | sorted by createdAt(descending)
    pending_sent_leaves = Leave.objects.filter(user=user, status="pending").order_by(
        "-createdAt"
    )
    other_sent_leaves = (
        Leave.objects.filter(user=user).exclude(status="pending").order_by("-createdAt")
    )
    sent_leave_req = (
        LeaveSerializer(pending_sent_leaves, many=True).data
        + LeaveSerializer(other_sent_leaves, many=True).data
    )

    received_leave_req = None

    # Received Leave Requests | pending first | sorted by createdAt(descending)
    if user.is_staff:
        pending_received_leaves = (
            Leave.objects.exclude(user=user)
            .filter(status="pending")
            .order_by("-createdAt")
        )
        other_received_leaves = (
            Leave.objects.exclude(user=user)
            .exclude(Q(status="pending") | Q(status="withdrawn"))
            .order_by("-createdAt")
        )
        received_leave_req = (
            LeaveSerializer(pending_received_leaves, many=True).data
            + LeaveSerializer(other_received_leaves, many=True).data
        )
    elif user.isSupervisor:
        supervision_users = User.objects.filter(supervisors__id=user.id)
        pending_received_leaves = (
            Leave.objects.filter(user__in=supervision_users)
            .filter(status="pending")
            .order_by("-createdAt")
        )
        other_received_leaves = (
            Leave.objects.filter(user__in=supervision_users)
            .exclude(Q(status="pending") | Q(status="withdrawn"))
            .order_by("-createdAt")
        )
        received_leave_req = (
            LeaveSerializer(pending_received_leaves, many=True).data
            + LeaveSerializer(other_received_leaves, many=True).data
        )

    res_body = {
        "sentReq": sent_leave_req,
        "receivedReq": received_leave_req,
    }
    return Response(res_body)
