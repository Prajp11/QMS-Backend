from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from api.models import UserProfile


class Command(BaseCommand):
    help = 'Create missing UserProfile instances for existing users'

    def handle(self, *args, **options):
        users_without_profile = []
        
        for user in User.objects.all():
            if not hasattr(user, 'profile'):
                users_without_profile.append(user)
                UserProfile.objects.create(user=user)
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created profile for user: {user.username}')
                )
        
        if not users_without_profile:
            self.stdout.write(
                self.style.SUCCESS('✅ All users already have profiles!')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Created {len(users_without_profile)} user profile(s)'
                )
            )
