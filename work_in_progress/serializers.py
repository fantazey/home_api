from rest_framework import serializers

from .models import Model, UserModelStatus, ModelGroup, KillTeam, BSUnit, BSCategory


class UserModelGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelGroup
        fields = ['id', 'name']


class BSUnitSerializer(serializers.ModelSerializer):
    bs_category = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = BSUnit
        fields = ['id', 'name', 'bs_category']


class BSCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BSCategory
        fields = ['id', 'name']


class KillTeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = KillTeam
        fields = ['id', 'name']


class UserModelStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModelStatus
        fields = ['id', 'name', 'order']

#######


class UserModelStatusIdSerializer(serializers.SlugRelatedField):

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

    def get_queryset(self):
        request = self.context['request']
        return UserModelStatus.objects.filter(user=request.user)

    class Meta:
        model = UserModelStatus
        fields = ['id']


class ModelSerializer(serializers.HyperlinkedModelSerializer):
    user_status_id = UserModelStatusIdSerializer(read_only=False, source='user_status', slug_field='id')
    user_status_name = serializers.SlugRelatedField(read_only=True, source='user_status', slug_field='name')
    groups = UserModelGroupSerializer(read_only=False, many=True)
    battlescribe_unit_id = serializers.SlugRelatedField(read_only=False, source='battlescribe_unit', slug_field='id', queryset=BSUnit.objects.all())
    battlescribe_unit_name = serializers.SlugRelatedField(read_only=True, source='battlescribe_unit', slug_field='name')
    kill_team_id = serializers.SlugRelatedField(read_only=False, source='kill_team', slug_field='id', queryset=KillTeam.objects.all())
    kill_team_name = serializers.SlugRelatedField(read_only=True, source='kill_team', slug_field='name')
    hours_spent = serializers.FloatField(read_only=True, source='get_hours_spent')

    class Meta:
        model = Model
        fields = [
            'id',
            'name',
            'unit_count',
            'terrain',
            'get_last_image_url',
            'user_status_id',
            'user_status_name',
            'groups',
            'battlescribe_unit_id',
            'battlescribe_unit_name',
            'kill_team_id',
            'kill_team_name',
            'hours_spent',
        ]


