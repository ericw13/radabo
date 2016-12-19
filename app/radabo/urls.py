from django.conf.urls import url
from radabo import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^prioritization/?$', views.Priority, name='priority'),
    url(r'^dashboard/?$', views.Dashboard, name='dashboard'),
    url(r'^enhancements/release/?$', views.ReleaseReport, name='release'),
    url(r'^enhancements/release/chart/?$', views.enhGraph, name='releasechart'),
    url(r'^enhancements/sprint/?$', views.SprintReport, name='sprint'),
    url(r'^enhancements/pending/?$', views.PendingUAT, name='UAT'),
    url(r'^enhancements/backlog/?$', views.Backlog, name='backlog'),
    url(r'^enhancements/backlog/(?P<chartType>[a-zA-Z]+)/?$', views.BacklogGraphs, name='blgraphs'),
    url(r'^enhancements/bymodule/?$', views.enhByModule, name='allbymod'),
    url(r'^enhancements/other/?$', views.NonFinance, name='nonfin'),
    url(r'^backlog/(?P<chartType>[a-zA-Z]+)/?$', views.BacklogGraphs, name='oldblgraphs'),
    url(r'^projects/grooming/?$', views.ProjectGrooming, name='projectGrooming'),
    url(r'^projects/active/(?P<epic>E[0-9]+)/?$', views.ProjectStories, name='projectStories'),
    url(r'^projects/active/?$', views.EpicView, name='activeProjects'),
    url(r'^velocity/old/?$', views.OldVelocityChart, name='oldvelocity'),
    url(r'^velocity/?$', views.VelocityChart, name='velocity'),
    url(r'^sprint/?$', views.FullSprint, name='full_sprint'),
    url(r'^syncstory/?$', views.updateStory, name='updateStory'),
    url(r'^info/?$', views.Info, name='info'),
]
