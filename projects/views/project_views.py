from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework import status
from django.db.models import Q
import json

from accounts.models import HubStaffConfig, User
from accounts.utils.user_helper import (
    get_hubStaff_user_by_email,
    get_avaza_users,
    get_avaza_user_by_email,
)

from ..models import Project
from ..utils.project_helper import (
    get_hubStaff_projects_from_api,
    get_project_users,
    get_avaza_projects_from_api,
    hubStaff_update_project_member,
    assign_avaza_project,
    get_object_by_key_value,
    create_avaza_project,
    create_hubStaff_project,
)
from ..serializers import ProjectSerializer, UserProjectSerializer


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def sync_projects(request):
    try:
        hubStaff_projects = get_hubStaff_projects_from_api()
        avaza_projects = get_avaza_projects_from_api()

        combined_projects = []

        for hubStaff_project in hubStaff_projects:
            avaza_project = next(
                (p for p in avaza_projects if p["Title"] == hubStaff_project["name"]),
                None,
            )
            combined_project = {
                "name": hubStaff_project.get("name"),
                "hubStaffId": hubStaff_project.get("id"),
                "avazaId": avaza_project.get("ProjectID") if avaza_project else None,
                "isActive": hubStaff_project.get("status") == "active"
                if hubStaff_project.get("status")
                else None,
            }
            combined_projects.append(combined_project)

        for avaza_project in avaza_projects:
            hubStaff_project = next(
                (p for p in hubStaff_projects if p["name"] == avaza_project["Title"]),
                None,
            )
            if not hubStaff_project:
                combined_project = {
                    "name": avaza_project.get("Title"),
                    "hubStaffId": None,
                    "avazaId": avaza_project.get("ProjectID"),
                    "isActive": not avaza_project.get("isArchived"),
                }
                combined_projects.append(combined_project)

        existing_projects = Project.objects.values_list("name", flat=True)
        to_create = []
        to_update = []

        for item in combined_projects:
            if item["name"] not in existing_projects:
                to_create.append(
                    Project(
                        name=item["name"],
                        hubStaffId=item.get("hubStaffId"),
                        avazaId=item.get("avazaId"),
                        users=get_project_users(
                            {
                                "hubStaffId": item.get("hubStaffId"),
                                "avazaId": item.get("avazaId"),
                            }
                        ),
                        isActive=item.get("isActive"),
                    )
                )
            else:
                to_update.append(
                    Project(
                        id=Project.objects.filter(name=item["name"]).first().id,
                        name=item["name"],
                        users=get_project_users(
                            {
                                "hubStaffId": item.get("hubStaffId"),
                                "avazaId": item.get("avazaId"),
                            }
                        ),
                        hubStaffId=item.get("hubStaffId"),
                        avazaId=item.get("avazaId"),
                        isActive=item.get("isActive"),
                    )
                )

        Project.objects.bulk_create(to_create)
        Project.objects.bulk_update(to_update, ["name", "isActive", "users"])

        # message = {"detail": "Projects synced successfully"}
        # return Response(message)
        serializer = ProjectSerializer(Project.objects.all(), many=True)
        return Response(serializer.data)
    except Exception as e:
        print(str(e))
        message = {"detail": "Error syncing projects"}
        return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_projects(request):
    email = request.GET.get("email")
    projects = None
    if email:
        projects = Project.objects.filter(
            users__contains=f'"email": "{email}"'
        )  # because users is in string format
        serializer = UserProjectSerializer(
            projects, many=True, context={"email": email}
        )
        return Response(serializer.data)
    else:
        projects = Project.objects.all()
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_my_projects(request):
    projects = Project.objects.filter(
        users__contains=f'"email": "{request.user.email}"'
    )
    serializer = ProjectSerializer(projects, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def get_project_by_id(request, id):
    try:
        project = Project.objects.get(id=id)
        serializer = ProjectSerializer(project, many=False)
        return Response(serializer.data)
    except Project.DoesNotExist:
        message = {"detail": "Project does not exist"}
        return Response(message, status=status.HTTP_404_NOT_FOUND)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_project_member(request):
    data = request.data

    hubStaff_data = data.get("hubStaff")
    hubStaff_user_email = hubStaff_data.get("email")
    hubStaff_project_id = hubStaff_data.get("projectId")
    hubStaff_user_role = hubStaff_data.get("userRole")

    avaza_data = data.get("avaza")
    avaza_user_email = avaza_data.get("email")
    avaza_project_id = avaza_data.get("projectId")

    if hubStaff_data and avaza_data and hubStaff_data["email"] != avaza_data["email"]:
        message = {"detail": "HubStaff and avaza user must be same"}
        return Response(message, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=hubStaff_user_email)
    except User.DoesNotExist:
        message = {"detail": "User does not exist"}
        return Response(message, status=status.HTTP_404_NOT_FOUND)

    hubStaff_success = False
    avaza_success = False

    if request.user.is_staff or (
        request.user.isSupervisor and request.user.is_supervisor_of(user)
    ):
        # HubStaff
        try:
            if (
                hubStaff_data
                and hubStaff_user_email
                and hubStaff_project_id
                and hubStaff_user_role
            ):
                hubStaff_user = get_hubStaff_user_by_email(hubStaff_user_email)
                if not hubStaff_user:
                    message = {
                        "detail": "This user is currently unavailable on hubStaff"
                    }
                    return Response(message, status=status.HTTP_404_NOT_FOUND)

                hubStaff_user_id = hubStaff_user["hubStaffId"]

                # hubStaff_user = get_hubStaff_user_by_id(hubStaff_user_id)
                # if not hubStaff_user:
                #     message = {
                #         "detail": "This user is currently unavailable on hubStaff"}
                #     return Response(message, status=status.HTTP_404_NOT_FOUND)

                hubStaff_update_project_member(
                    hubStaff_user_id, hubStaff_user_role, hubStaff_project_id
                )

                hubStaff_project = Project.objects.get(hubStaffId=hubStaff_project_id)

                hubStaff_project_users = json.loads(hubStaff_project.users)

                existing_user_obj = get_object_by_key_value(
                    hubStaff_project_users, "email", hubStaff_user_email
                )

                if hubStaff_user_role == "remove":
                    # Remove the object based on hubStaffId
                    if existing_user_obj and existing_user_obj.get("avazaId"):
                        existing_user_obj["hubStaffId"] = None
                        hubStaff_project_users.append(existing_user_obj)
                    else:
                        hubStaff_project_users = [
                            item
                            for item in hubStaff_project_users
                            if item["email"] != hubStaff_user_email
                        ]

                else:
                    if existing_user_obj:
                        existing_user_obj["hubStaffId"] = hubStaff_user["hubStaffId"]
                        hubStaff_project_users.append(existing_user_obj)
                    else:
                        hubStaff_project_users.append(hubStaff_user)

                hubStaff_project.users = json.dumps(hubStaff_project_users)
                hubStaff_project.save()

                hubStaff_success = True

                # If un-assigning the project, then don't go to Avaza, because it's not possible according to current API documentation
                if hubStaff_user_role == "remove":
                    message = {
                        "detail": "Project unassigned successfully from HubStaff"
                    }
                    return Response(message)
        except:
            pass

            # Avaza
        try:
            if avaza_data and avaza_user_email and avaza_project_id:
                avaza_user = get_avaza_user_by_email(avaza_user_email)
                if not avaza_user:
                    message = {
                        "detail": "Project assigned successfully on HubStaff, but this user is currently unavailable on Avaza"
                    }
                    return Response(message, status=status.HTTP_404_NOT_FOUND)

                avaza_user_id = avaza_user["UserID"]

                assign_avaza_project(avaza_user_id, avaza_project_id)

                avaza_project = Project.objects.get(avazaId=avaza_project_id)

                avaza_project_users = json.loads(avaza_project.users)

                existing_user_obj = get_object_by_key_value(
                    avaza_project_users, "email", avaza_user_email
                )
                if existing_user_obj:
                    existing_user_obj["avazaId"] = avaza_user["UserID"]
                    avaza_project_users.append(existing_user_obj)
                else:
                    avaza_project_users.append(avaza_user)

                avaza_project.users = json.dumps(avaza_project_users)
                avaza_project.save()

                avaza_success = True
        except:
            pass

        if hubStaff_success and avaza_success:
            message = {"detail": "Project assigned successfully"}
            return Response(message)
        elif hubStaff_success:
            message = {"detail": "Project assigned successfully on HubStaff"}
            return Response(message)
        elif avaza_success:
            message = {"detail": "Project assigned successfully on Avaza"}
            return Response(message)
        else:
            message = {"detail": "Project assignment failed"}
            return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    else:
        message = {"detail": "You do not have permission to perform this action"}
        return Response(message, status=status.HTTP_403_FORBIDDEN)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def create_project(request):
    data = request.data
    title = data.get("title")
    avaza_company = data.get("avazaCompany")

    try:
        hubStaff_proj = create_hubStaff_project(title)
        avaza_proj = create_avaza_project(title, avaza_company)

        project = Project.objects.create(
            name=title,
            hubStaffId=hubStaff_proj.get("id"),
            avazaId=avaza_proj.get("ProjectID"),
            users=json.dumps(
                [
                    {
                        "avazaId": user["UserIDFK"],
                        "email": user["Email"],
                        "name": user["Fullname"],
                    }
                    for user in avaza_proj["Members"]
                ]
            ),
        )

        serializer = ProjectSerializer(project, many=False)

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except Exception as e:
        message = {"detail": str(e)}
        return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
