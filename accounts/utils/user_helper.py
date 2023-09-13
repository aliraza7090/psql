from django.core.mail import send_mail
import re
import string
from random import choice, randint
from django.core.validators import validate_email
import requests

from ..models import HubStaffConfig, AvazaConfig


def send_email_custom(subject, body, recipients):
    send_mail(subject=subject, message=body, from_email="deck.eportal@gmail.com", recipient_list=recipients,
              fail_silently=False,
              )


def validate_password(password):
    while True:
        if re.search("[\"'/\\\`]", password):
            return (
                False,
                "\/'` are not allowed in password",
            )

        elif len(password.strip()) < 8 or not (
            re.search("[0-9]", password)
            and re.search("[a-z]", password)
            and re.search("[A-Z]", password)
            and re.search(
                "[$&+,:;=?@#|<>.^*()%!-/_/g]", password
            )  # [/_/g] to match an underscore
        ):
            return (
                False,
                "Use 8 or more characters, must include a capital letter, a number, and a special character",
            )
        else:
            return (True, "Your password seems fine")


def generate_random_password():
    characters = (
        string.ascii_letters
        + re.sub("[\"'/.\\\`;:,]", "", string.punctuation)
        + string.digits
    )  # re.sub('["]') -> here you can add which symbol you want to remove
    password = "".join(choice(characters) for x in range(randint(8, 16)))
    return password


def is_email_valid(email):
    try:
        validate_email(email)
        return True
    except:
        return False


def get_hubStaff_users():
    config = HubStaffConfig.load()

    users_url = f"{config.baseUrl}/organizations/{config.organizationId}/members?include=users"
    headers = {"authorization": f"Bearer {config.accessToken}"}

    response = requests.get(users_url, headers=headers)

    if response.status_code == 200:
        res_json = response.json()
        return res_json["users"]
    else:
        raise Exception()


def get_hubStaff_user_by_email(email):
    hubStaff_users = get_hubStaff_users()

    for user in hubStaff_users:
        if user["email"] == email:
            return {"hubStaffId": user["id"],
                    "name": user["name"],
                    "email": user["email"]}


def get_hubStaff_user_by_id(user_id):
    config = HubStaffConfig.load()

    url = f"{config.baseUrl}/users/{user_id}"
    headers = {"authorization": f"Bearer {config.accessToken}"}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        user = response.json()["user"]
        return {"hubStaffId": user["id"],
                "name": user["name"],
                "email": user["email"]}
    else:
        raise Exception()


def get_avaza_users():
    config = AvazaConfig.load()
    
    url = f"{config.baseUrl}/UserProfile"
    headers = {"authorization": f"Bearer {config.accessToken}"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()["Users"]
    else:
        raise Exception()
    

def get_avaza_user_by_email(email):
    users = get_avaza_users()
    
    for user in users:
        if user["Email"] == email:
            print("Avaza user", user)
            return user
    
    