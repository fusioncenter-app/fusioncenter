import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from custom_user.models import User, Profile

class Command(BaseCommand):
    help = 'Create sample users for testing'

    def add_arguments(self, parser):
        parser.add_argument('total', type=int, help='Indicates the number of users to be created')

    def handle(self, *args, **kwargs):
        total = kwargs['total']

        for i in range(total):
            # Customize user data as needed
            email = f'user{i}@example.com'
            password = 'Deseas123'
            first_name = f'First{i}'
            last_name = f'Last{i}'
            birth_day = timezone.now().date() - timezone.timedelta(days=random.randint(365 * 18, 365 * 70))
            phone_number = f'123456789{i:03}'
            country = 'Argentina'
            state = 'Buenos Aires'
            city = f'City{i}'
            address = f'Street {i}'
            zip_code = f'12345{i:02}'
            time_zone = 'America/Argentina/Buenos_Aires'

            # Check if a user with the given email already exists
            user, created = User.objects.get_or_create(email=email, defaults={'password': password})

            # Check if a profile already exists for the user
            if not hasattr(user, 'profile'):
                Profile.objects.create(
                    user=user,
                    first_name=first_name,
                    last_name=last_name,
                    birth_day=birth_day,
                    phone_number=phone_number,
                    country=country,
                    state=state,
                    city=city,
                    address=address,
                    zip_code=zip_code,
                    time_zone=time_zone,
                )

                self.stdout.write(self.style.SUCCESS(f'Successfully created user: {user}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'User with email {email} already exists. Skipping creation.'))
