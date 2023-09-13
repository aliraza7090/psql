import math
from datetime import datetime


def calculate_leaves(join_date_str, job_type, isAnnualAllowed):
    current_date_str = datetime.now().strftime(
        "%Y-%m-%d"
    )  # get current date programmatically

    join_date = datetime.strptime(join_date_str, "%Y-%m-%d").date()
    current_date = datetime.strptime(current_date_str, "%Y-%m-%d").date()

    # calculate the difference between the two dates in months
    months = (current_date.year - join_date.year) * 12 + (
        current_date.month - join_date.month
    )
    # add remaining months of current year
    if current_date.month < 12:
        months += 12 - current_date.month

    obj = {
        "sickAllowed": 8,
        "casualAllowed": 10,
        "annualAllowed": 14,
    }

    if months < 12 and isAnnualAllowed:
        obj["sickAllowed"] = math.ceil((8 / 12) * months)
        obj["casualAllowed"] = math.ceil((10 / 12) * months)
        obj["annualAllowed"] = math.ceil((14 / 12) * months)

    elif months < 12:
        obj["sickAllowed"] = math.ceil((8 / 12) * months)
        obj["casualAllowed"] = math.ceil((10 / 12) * months)
        obj["annualAllowed"] = 0

    if job_type.lower().replace("_", " ") == "part time":
        obj["sickAllowed"] = math.ceil(obj["sickAllowed"] / 2)
        obj["casualAllowed"] = math.ceil(obj["casualAllowed"] / 2)
        obj["annualAllowed"] = math.ceil(obj["annualAllowed"] / 2)

    if job_type.lower() == "intern":
        obj["sickAllowed"] = 0
        obj["casualAllowed"] = 2
        obj["annualAllowed"] = 0

    return obj


def send_update_leave_notification_email(leave, user, frontend_url):
    # Send email notification
    email_subject = f"""Leave Status | {leave.status.title()} | {
                    leave.startDate if leave.startDate == leave.endDate 
                                else leave.startDate.strftime('%Y-%m-%d') + ' to ' + leave.endDate.strftime('%Y-%m-%d')}"""
    email_message = f"""Your {
        leave.leaveType
        } leave request has been {leave.status.title()} for {
        leave.startDate if leave.startDate == leave.endDate 
                                else leave.startDate.strftime('%Y-%m-%d') + ' to ' + leave.endDate.strftime('%Y-%m-%d')
        } ({leave.days} day) by {user.first_name} ({user.designation}). Please visit {frontend_url}req_listing/{leave.id} for more details.
        """
    leave.user.send_email(email_subject, email_message)
