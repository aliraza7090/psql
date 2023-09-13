import requests
from django.core.management.base import BaseCommand
from accounts.models import HubStaffConfig


class Command(BaseCommand):
    help = 'Refreshes the HubStaff tokens'

    def handle(self, *args, **options):
        config = HubStaffConfig.load()
        refresh_token = config.refreshToken

        # Make a request to get the new tokens using the refresh token
        response = requests.post(
            f'https://account.hubstaff.com/access_tokens?grant_type=refresh_token&refresh_token={refresh_token}', data={})

        try:
            # Process the response and store the result
            if response.status_code == 200:
                resp_json = response.json()
                config.accessToken = resp_json.get("access_token")
                config.refreshToken = resp_json.get("refresh_token")
                config.save()

                self.stdout.write(self.style.SUCCESS(
                    'HubStaff tokens has been updated successfully!'))
            else:
                raise Exception(response.json()["error_description"])

        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f"HubStaff tokens update failed. {str(e)}"))
