import django
django.setup()

from models import FileTransfer, TransferLocation

class Transfer:

    def __init__(self, **kwargs):
        if 'file_id' in kwargs:
            self.file_id = kwargs.pop('file_id')
        if 'filename' in kwargs:
            self.filename = kwargs.pop('filename')
        if 'loc_code' in kwargs:
            self.loc_code = kwargs.pop('loc_code')

    def add(self):
        if not self.loc_code or not self.filename:
            raise Exception("Cannot add without a location and filename")   
        try:
            l = TransferLocation.objects.filter(location_code=self.loc_code)
            f = FileTransfer()
            f.location = l[0]
            f.filename = self.filename
            f.status = 'N'
            f.save()
        except Exception as e:
            raise Exception("%s (%s)" % (e.message, type(e)))

    def get(self):
        if not self.file_id:
            raise Exception("file_id not defined")
        try:
            results = FileTransfer.objects.filter(pk=self.file_id)
            return results[0]
        except Exception as e:
            raise Exception("%s (%s)" % (e.message, type(e)))
