#!/usr/bin/python
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "xfr.settings")
import django
django.setup()
from metrics.models import Sprint
from metrics.utils import getSprint, initRally

rally=initRally()

response = rally.get('Iteration',fetch="Name,StartDate,EndDate,PlanEstimate,State")

for sprint in response:
    this=getSprint(sprint.Name)
    if this == None:
      # Create new instance
       this = Sprint(name=sprint.Name,
                     startDate=sprint.StartDate,
                     endDate=sprint.EndDate,
                     velocity=sprint.PlanEstimate,
                     status=sprint.State)
    else:
       this.startDate = sprint.StartDate
       this.endDate = sprint.EndDate
       this.velocity = sprint.PlanEstimate
       this.status = sprint.State

    this.save()
