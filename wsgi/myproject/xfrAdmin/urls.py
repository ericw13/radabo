from django.conf.urls import url
from xfrAdmin import views, forms

urlpatterns = [
    url(r'^index/$', views.index, name='index'),
    url(r'^main/$', views.startpage, name='startpage'),
    url(r'^logout/$', views.logout_view),
    url(r'^transfers/$', views.TransferList.as_view()),
    url(r'^addxfr/$', views.AddTransfer.as_view()),
    url(r'^transfers/page/(?P<page>[0-9]+)/$', views.TransferList.as_view()),
    url(r'^errors/$', views.ErrorList.as_view()),
    url(r'^errors/recent/$', views.RecentErrorList.as_view()),
    url(r'^transfers/(?P<pk>[0-9]+)/$', views.TransferDetail.as_view()),
    url(r'^search/$', views.search, name='search'),
]

