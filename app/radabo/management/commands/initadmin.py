from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.conf import settings
"""
Command to create an admin user for each value in settings.ADMINS.  This is
useful for an initial deployment in a Docker container
"""

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        if User.objects.count() == 0:
            for user in settings.ADMINS:
                username = user.get('uid')
                email = user.get('email')
                password = 'admin'
                print "Found %s <%s>" % (username, email)
                admin = User.objects.create_superuser(
                            email=email,
                            username=username,
                            password=password)
                admin.is_active = True
                admin.is_admin = True
                admin.save()
        else:
            print "Admin accounts are only created when no Users exist"
                
