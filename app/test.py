from radabo.utils import initRally as r
srv=r()
query='Feature.Parent.FormattedId = "E759"'
fetch="FormattedID,Name,ScheduleState,PlanEstimate,Feature,Owner"
data=srv.get('User Story',query=query,fetch=fetch,order="Feature")

for x in data:
  print x.FormattedID, x.Feature.Parent.Name
