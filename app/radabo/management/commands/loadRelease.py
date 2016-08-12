from django.core.management.base import BaseCommand, CommandError
from radabo.models import Release
from radabo.utils import getRelease, initRally

"""
This command loads Release information from Rally and stores it in the database
"""
class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        rallyServer=initRally()

        q = ['Name contains "Enh Release"',
             'ReleaseStartDate > "2016-01-01T00:00:00.000Z"'
            ]
        response = rallyServer.get(
                       'Release',
                       query=q,
                       fetch="Name,ReleaseStartDate,ReleaseDate,State"
                   )
        for release in response:
            this=getRelease(release.Name)
            if this == None:
              # Create new instance
               this = Release(name=release.Name,
                             startDate=release.ReleaseStartDate,
                             endDate=release.ReleaseDate,
                             status=release.State)
            else:
               this.startDate = release.ReleaseStartDate
               this.endDate = release.ReleaseDate
               this.status = release.State

            this.save()
