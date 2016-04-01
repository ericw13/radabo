from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import render, render_to_response
from django.template import RequestContext, loader
from django.views import generic
from django.utils.html import escape
from xfrAdmin.serializers import TransferSerializer
from xfrAdmin.models import FileTransfer, TransferLocation
from xfrAdmin.forms import SearchForm
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
import datetime

# Create your views here.

def index(request):
    t = loader.get_template('xfrAdmin/index.html')
    c = {}
    return HttpResponse(t.render(c, request))

def logout_view(request):
    logout(request)
    t = loader.get_template('xfrAdmin/index.html')
    c = {}
    return HttpResponse(t.render(c, request))

@login_required
def startpage(request):
    t = loader.get_template('xfrAdmin/main.html')
    c = {}
    return HttpResponse(t.render(c, request))

@login_required
class TransferView(generic.ListView):
    template_name = 'xfrAdmin/transfer.html'
    context_object_name = 'xfr'

    def get_queryset(self):
        return FileTransfer.objects.filter().order_by('-last_update_date')[:25]

def routeToError(request):
    t = loader.get_template('xfrAdmin/error.html')
    c = {}
    return HttpResponse(t.render(c, request))

def search(request):
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            kwargs = {}
            if 'filename' in request.POST and request.POST['filename']:
                kwargs['filename__icontains'] = request.POST['filename']
            if 'status' in request.POST and request.POST['status']:
                kwargs['status'] = request.POST['status']
            results = FileTransfer.objects.filter( **kwargs ).order_by('-last_update_date')[:25]
            return render_to_response('xfrAdmin/transfer.html',
                      RequestContext(request, {
                          'form': form,
                          'xfr': results
                      } ) )
        else:
            return HttpResponse("This failed miserably, %s." % request.method)
    else:
        return render(request, 'xfrAdmin/search.html', {'form': SearchForm()})
            
class TransferList(LoginRequiredMixin, APIView):

  login_url = '/accounts/login/'
  redirect_field_name = 'redirect_to'

  def get(self, request, page=1, format=None):
    MAXROWS = 25
    page=int(page)
    if page <= 0:
        return HttpResponse("You are not allowed to view pages less than 1.")
    iMin=(page - 1) * MAXROWS
    iMax=iMin+(MAXROWS)
    nextPage=page+1
    prevPage=page-1

    t = loader.get_template('xfrAdmin/transfer.html')
    transfers = FileTransfer.objects.all().order_by('-last_update_date')[iMin:iMax]
    rowcount=len(transfers)
    if rowcount < MAXROWS-1:
        nextPage = 0
    c = {'xfr': transfers, 'next_page':nextPage, 'prev_page':prevPage, 'rowcount':rowcount, 'no_message':'No transfers can be found.'}
    return HttpResponse(t.render(c, request))

class AddTransfer(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        return routeToError(request)

    def post(self, request, format=None):
        serializer = TransferSerializer(data=request.data)
        if serializer.is_valid():
          serializer.save()
          return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TransferDetail(APIView):

    permission_classes = (IsAuthenticated,)
    def get_object(self, pk):
        try:
            return FileTransfer.objects.get(pk=pk)
        except FileTransfer.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        """
        xfr = self.get_object(pk)
        serializer = TransferSerializer(xfr)
        return Response(serializer.data)
        """
        return routeToError(request)

    def put(self, request, pk, format=None):
        xfr = self.get_object(pk)
        rdata = JSONParser().parse(request)
        fname=rdata['filename'] if 'filename' in rdata else xfr.filename
        loc_code=rdata['location'] if 'location' in rdata else xfr.location
        status_code=rdata['status'] if 'status' in rdata else xfr.status
        error_message=rdata['error_message'] if 'error_message' in rdata else xfr.error_message

        data = {'filename': fname,
                'location': loc_code,
                'status': status_code,
                'error_message': error_message}
        serializer = TransferSerializer(xfr, data=data)
        if serializer.is_valid():
          serializer.save()
          return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        xfr = self.get_object(pk)
        xfr.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ErrorList(LoginRequiredMixin, APIView):

    login_url = '/accounts/login/'
    redirect_field_name = 'redirect_to'

    def get(self, request, format=None):
        t = loader.get_template('xfrAdmin/transfer.html')
        transfers = FileTransfer.objects.filter(status='E').order_by('-last_update_date')[:25]
        c = {'xfr': transfers, 'no_message':'No errors found in the system.'}
        return HttpResponse(t.render(c, request))
    """
    serializer = TransferSerializer(transfers, many=True)
    return Response(serializer.data)
    """

class RecentErrorList(LoginRequiredMixin, APIView):

    login_url = '/accounts/login/'
    redirect_field_name = 'redirect_to'

    def get(self, request, format=None):
        t = loader.get_template('xfrAdmin/transfer.html')
        filterdate = datetime.datetime.now() - datetime.timedelta(days=1)
        transfers = FileTransfer.objects.filter(status='E',last_update_date__gte=filterdate).order_by('-last_update_date')[:25]
        c = {'xfr': transfers, 'no_message':'No errors have occurred in the past 24 hours.'}
        return HttpResponse(t.render(c, request))
     
