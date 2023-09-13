import requests
from accounts.models import HubStaffConfig, AvazaConfig
import json


def get_hubStaff_projects_from_api():
    config = HubStaffConfig.load()

    projects_url = f"{config.baseUrl}/organizations/{config.organizationId}/projects?page_limit=500"
    headers = {"authorization": f"Bearer {config.accessToken}"}

    response = requests.get(projects_url, headers=headers)

    if response.status_code == 200:
        res_json = response.json()
        return res_json["projects"]
    else:
        raise Exception()


def get_avaza_projects_from_api():
    config = AvazaConfig.load()

    projects_url = f"{config.baseUrl}/Project?pageSize=1000"
    headers = {"authorization": f"Bearer {config.accessToken}"}
    response = requests.get(projects_url, headers=headers)

    if response.status_code == 200:
        res_json = response.json()
        return res_json["Projects"]
    else:
        raise Exception()


def get_project_users(data):
    project_hubStaff_id = data["hubStaffId"]
    project_avaza_id = data["avazaId"]

    hubStaff_config = HubStaffConfig.load()
    avaza_config = AvazaConfig.load()

    resp_data = []

    if project_hubStaff_id:
        project_users_url = f"{hubStaff_config.baseUrl}/projects/{project_hubStaff_id}/members?include_removed=false&include=users"
        headers = {"authorization": f"Bearer {hubStaff_config.accessToken}"}

        response = requests.get(project_users_url, headers=headers)

        if response.status_code == 200:
            for user in response.json()["users"]:
                resp_data.append(
                    {
                        "hubStaffId": user["id"],
                        "name": user["name"],
                        "email": user["email"],
                    }
                )

    if project_avaza_id:
        project_users_url = (
            f"{avaza_config.baseUrl}/ProjectMember?ProjectID={project_avaza_id}"
        )
        headers = {"authorization": f"Bearer {avaza_config.accessToken}"}

        response = requests.get(project_users_url, headers=headers)

        if response.status_code == 200:
            for user in response.json()["ProjectMembers"]:
                index = get_index_by_key_value(resp_data, "email", user["Email"])
                if index is not None:
                    resp_data[index]["avazaId"] = user["UserIDFK"]
                else:
                    resp_data.append(
                        {
                            "avazaId": user["UserIDFK"],
                            "email": user["Email"],
                            "name": user["Fullname"],
                        }
                    )

    return json.dumps(resp_data)


def get_index_by_key_value(array, key, value):
    for i, dictionary in enumerate(array):
        if dictionary.get(key) == value:
            return i
    return None


def hubStaff_update_project_member(user_id, user_role, project_id):
    config = HubStaffConfig.load()
    url = f"{config.baseUrl}/projects/{project_id}/update_members"
    headers = {"authorization": f"Bearer {config.accessToken}"}

    req_obj = {"members": [{"user_id": user_id, "role": user_role}]}
    response = requests.put(url, headers=headers, json=req_obj)

    if response.status_code == 200:
        return "success"
    else:
        raise Exception()


def assign_avaza_project(user_id, project_id):
    config = AvazaConfig.load()
    url = f"{config.baseUrl}/ProjectMember"
    headers = {"authorization": f"Bearer {config.accessToken}"}

    req_obj = {
        "UserIDFK": user_id,
        "ProjectIDFK": project_id,
    }

    response = requests.post(url, headers=headers, json=req_obj)

    if response.status_code == 200:
        return "success"
    else:
        print(response.text)
        raise Exception()


def get_object_by_key_value(lst, key, value):
    for obj in lst:
        if obj.get(key) == value:
            return obj
    return None


def get_avaza_companies():
    config = AvazaConfig.load()
    url = f"{config.baseUrl}/Company"
    headers = {"authorization": f"Bearer {config.accessToken}"}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()["Companies"]
    else:
        raise Exception()


def create_avaza_project(title, companyName):
    companies = get_avaza_companies()

    CompanyIDFK = None

    for company in companies:
        if company["CompanyName"] == companyName:
            CompanyIDFK = company["CompanyID"]

    req_obj = {"ProjectTitle": title, "PopulateDefaultProjectMembers": False}

    if CompanyIDFK:
        req_obj["CompanyIDFK"] = CompanyIDFK
    else:
        req_obj["CompanyName"] = companyName

    config = AvazaConfig.load()
    url = f"{config.baseUrl}/Project"
    headers = {"authorization": f"Bearer {config.accessToken}"}

    response = requests.post(url, headers=headers, json=req_obj)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception("Avaza: " + response.json()["title"])


def create_hubStaff_project(title):
    config = HubStaffConfig.load()
    url = f"{config.baseUrl}/organizations/{config.organizationId}/projects"
    headers = {"authorization": f"Bearer {config.accessToken}"}

    req_obj = {
        "name": title,
    }

    response = requests.post(url, headers=headers, json=req_obj)

    if response.status_code == 201:
        return response.json()["project"]
    else:
        raise Exception("HubStaff: " + response.json()["error"])
