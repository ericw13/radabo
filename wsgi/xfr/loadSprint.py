#!/usr/bin/python
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "xfr.settings")
import django
django.setup()
from metrics.models import Sprint
from metrics.utils import getSprint, initRally

rally=initRally()

q='(State = "Planning") OR (State = "Committed")'
response = rally.get('Iteration',fetch="Name,StartDate,EndDate,PlanEstimate,State")

x={}
# First, loop to sum velocity across common sprint name for various projects
for sprint in response:
    sprintName = str(sprint.Name)
    if sprintName not in x:
        x[sprintName] = {}
        x[sprintName]['Velocity'] = 0
        x[sprintName]['startDate'] = sprint.StartDate
        x[sprintName]['endDate'] = sprint.EndDate
        x[sprintName]['State'] = sprint.State

    if not sprint.PlanEstimate:
        sprint.PlanEstimate = 0

    x[sprintName]['Velocity'] = x[sprint.Name]['Velocity'] + sprint.PlanEstimate

for key in x:

    this=getSprint(key)
    if this == None:
      # Create new instance
       this = Sprint(name=key,
                     startDate=x[key]['startDate'],
                     endDate=x[key]['endDate'],
                     velocity=x[key]['Velocity'],
                     status=x[key]['State'])
    else:
       this.startDate = x[key]['startDate']
       this.endDate = x[key]['endDate']
       this.velocity = x[key]['Velocity']
       this.status = x[key]['State']

    this.save()

