"""
From a sample tutorial
from django.contrib.auth.models import User, Group
"""
from rest_framework import serializers
from xfrAdmin.models import FileTransfer, TransferLocation

"""
From a sample tutorial
class UserSerializer(serializers.HyperlinkedModelSerializer):
  class Meta:
    model=User
    fields = ('url','username','email','groups')

class GroupSerializer(serializers.HyperlinkedModelSerializer):
  class Meta:
    model = Group
    fields = ('url','name')
"""

class TransferSerializer(serializers.ModelSerializer):
  location = serializers.SlugRelatedField(
    many=False,
    queryset=TransferLocation.objects.all(),
    slug_field='location_code')

  class Meta:
    model = FileTransfer
    fields = ('id', 
              'location', 
              'filename', 
              'status', 
              'error_message', 
              'creation_date', 
              'last_update_date') 

  def create(self, validated_data):
    return FileTransfer.objects.create(**validated_data)

  def update(self, instance, validated_data):
    instance.location = validated_data.get('location', instance.location)
    instance.filename = validated_data.get('filename', instance.filename)
    instance.status = validated_data.get('status', instance.status)
    instance.error_message = validated_data.get('error_message', instance.error_message)
    instance.save()
    return instance
