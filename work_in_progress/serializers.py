from rest_framework import serializers

from .models import Model, UserModelStatus


class UserModelStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModelStatus
        fields = ['id', 'name', 'order']


class UserModelStatusIdSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModelStatus
        fields = ['id']


class ModelSerializer(serializers.HyperlinkedModelSerializer):
    user_status = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Model
        fields = ['id', 'name', 'get_last_image_url', 'user_status']
