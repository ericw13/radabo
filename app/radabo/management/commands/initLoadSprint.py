from django.core.management.base import BaseCommand, CommandError
from radabo.models import Sprint
from radabo.utils import getSprint, initRally

"""
This command retrieves Iteration details from Rally and loads them into the
Sprint table
"""
class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        rallyServer = initRally()

        # Need to load sprint data for all sprints
        q = 'StartDate > "2015-05-01T00:00:00.000Z"'
        response = rallyServer.get(
                       'Iteration',
                       query=q,
                       fetch="Name,StartDate,EndDate,PlanEstimate,State"
                   )

        x = {}
        # First, loop to sum velocity across common sprint name for 
        # various projects
        for sprint in response:
            sprintName = str(sprint.Name)
            if sprintName not in x:
                x[sprintName] = {
                    'Velocity': 0,
                    'startDate': sprint.StartDate,
                    'endDate': sprint.EndDate,
                    'State': sprint.State,
                }
            if not sprint.PlanEstimate:
                sprint.PlanEstimate = 0

            x[sprintName]['Velocity'] += sprint.PlanEstimate

        for key in x:

            this = getSprint(key)
            if this:
                # Update existing instance
                this.startDate=x[key]['startDate']
                this.endDate=x[key]['endDate']
                this.velocity=x[key]['Velocity']
                this.status=x[key]['State']
            else:
                # Create new instance
                this = Sprint(name=key,
                              startDate=x[key]['startDate'],
                              endDate=x[key]['endDate'],
                              velocity=x[key]['Velocity'],
                              status=x[key]['State'])

            this.save()
