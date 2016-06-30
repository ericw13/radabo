from django.conf.urls import url
from metrics import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^velocity/old/?$', views.OldVelocityChart, name='velocity'),
    url(r'^latestory/?$', views.DelayedItems, name='late'),
    url(r'^success/?$', views.Success, name='speedometer'),
    url(r'^release/?$', views.ReleaseReport, name='release'),
    url(r'^sprint/?$', views.SprintReport, name='sprint'),
    url(r'^backlog/?$', views.Backlog, name='backlog'),
    url(r'^backlog/(?P<chartType>[a-zA-Z]+)/?$', views.BacklogGraphs, name='blgraphs'),
    url(r'^projects/?$', views.ProjectGrooming, name='projects'),
    url(r'^syncstory/?$', views.updateStory, name='updateStory'),
]
