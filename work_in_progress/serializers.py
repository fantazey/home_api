from rest_framework import serializers, fields
from rest_framework.utils import html

from .models import Model, UserModelStatus, ModelGroup, KillTeam, BSUnit, BSCategory, ModelProgress, ModelImage


class UserModelGroupSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = ModelGroup
        fields = ['id', 'name']


class BSCategorySerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = BSCategory
        fields = ['id', 'name']


class BSUnitSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    bs_category = BSCategorySerializer()

    class Meta:
        model = BSUnit
        fields = ['id', 'name', 'bs_category']


class KillTeamSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = KillTeam
        fields = ['id', 'name']


class UserModelStatusSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = UserModelStatus
        fields = ['id', 'name', 'order', 'previous', 'next']

    def get_value(self, dictionary):
        if html.is_html_input(dictionary):
            return self.get_value_for_multipart(dictionary) or fields.empty
        return super().get_value(dictionary)

    def get_value_for_multipart(self, dictionary):
        key = 'user_status'
        user = self.context['request'].user
        item = UserModelStatus.objects.get(id=dictionary.get(key), user=user)
        return UserModelStatusSerializer(item).data


class ModelSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    user_status = UserModelStatusSerializer()
    groups = UserModelGroupSerializer(many=True)
    battlescribe_unit = BSUnitSerializer(required=False, allow_null=True)
    kill_team = KillTeamSerializer(required=False, allow_null=True)
    hours_spent = serializers.FloatField(read_only=True, source='get_hours_spent')
    get_last_image_url = serializers.CharField(read_only=True)

    class Meta:
        model = Model
        fields = [
            'id',
            'name',
            'buy_date',
            'unit_count',
            'terrain',
            'get_last_image_url',
            'user_status',
            'groups',
            'battlescribe_unit',
            'kill_team',
            'hours_spent',
        ]

    def get_value(self, dictionary):
        if html.is_html_input(dictionary):
            return self.get_value_for_multipart(dictionary) or fields.empty
        return super().get_value(dictionary)

    def get_value_for_multipart(self, dictionary):
        key = 'model'
        user = self.context['request'].user
        item = Model.objects.get(id=dictionary.get(key), user=user)
        return ModelSerializer(item).data

    def create(self, validated_data):
        request = self.context['request']
        user = request.user
        bs_unit_data = validated_data.pop('battlescribe_unit')
        kill_team_data = validated_data.pop('kill_team')
        groups_data = validated_data.pop('groups')
        status_data = validated_data.pop('user_status')
        model = Model(**validated_data)
        model.user = user
        model.user_status = UserModelStatus.objects.get(id=status_data.get('id'), user=user)

        if groups_data is not None:
            model_group_id = []
            for model_group_data_item in groups_data:
                model_group_id.append(model_group_data_item.get('id'))
            groups = ModelGroup.objects.filter(user=user, id__in=model_group_id)
            for group in groups:
                model.groups.add(group)

        if bs_unit_data is not None:
            model.battlescribe_unit = BSUnit.objects.get(id=bs_unit_data.get('id'))
        else:
            model.battlescribe_unit = None

        if kill_team_data is not None:
            model.kill_team = KillTeam.objects.get(id=kill_team_data.get('id'))
        else:
            model.kill_team = None

        model.save()
        return model

    def update(self, instance: Model, validated_data):
        request = self.context['request']
        user = request.user

        instance.name = validated_data.get('name', instance.name)
        instance.unit_count = validated_data.get('unit_count', instance.unit_count)
        instance.terrain = validated_data.get('terrain', instance.terrain)
        instance.buy_date = validated_data.get('buy_date', instance.buy_date)

        user_status_data: dict = validated_data.pop('user_status')
        if user_status_data is not None:
            instance.user_status = UserModelStatus.objects.get(id=user_status_data.get('id'), user=user)

        model_group_data: list = validated_data.pop('groups')
        if model_group_data is not None:
            model_group_id = []
            for model_group_data_item in model_group_data:
                model_group_id.append(model_group_data_item.get('id'))
            groups = ModelGroup.objects.filter(user=user, id__in=model_group_id)
            instance.groups.clear()
            for group in groups:
                instance.groups.add(group)

        bs_unit_data = validated_data.pop("battlescribe_unit")
        if bs_unit_data is not None:
            instance.battlescribe_unit = BSUnit.objects.get(id=bs_unit_data.get('id'))
        else:
            instance.battlescribe_unit = None

        kill_team_data = validated_data.pop("kill_team")
        if kill_team_data is not None:
            instance.kill_team = KillTeam.objects.get(id=kill_team_data.get('id'))
        else:
            instance.kill_team = None

        instance.save()
        return instance


class ModelProgressSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    user_status = UserModelStatusSerializer()
    get_last_image_url = serializers.CharField(read_only=True)
    description = serializers.CharField(required=False, allow_blank=True)
    model = ModelSerializer(write_only=True)

    class Meta:
        model = ModelProgress
        fields = [
            'id',
            'title',
            'description',
            'datetime',
            'time',
            'get_last_image_url',
            'user_status',
            'model'
        ]

    def create(self, validated_data):
        request = self.context['request']
        user = request.user
        status_data = validated_data.pop('user_status')
        model_data = validated_data.pop('model')
        instance = ModelProgress(**validated_data)
        instance.user_status = UserModelStatus.objects.get(id=status_data.get('id'), user=user)
        instance.model = Model.objects.get(id=model_data.get('id'), user=user)
        instance.save()
        return instance

    def update(self, instance: ModelProgress, validated_data):
        request = self.context['request']
        user = request.user

        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.time = validated_data.get('time', instance.time)
        instance.datetime = validated_data.get('datetime', instance.datetime)

        user_status_data: dict = validated_data.pop('user_status')
        if user_status_data is not None:
            instance.user_status = UserModelStatus.objects.get(id=user_status_data.get('id'), user=user)
        instance.save()
        return instance


class ModelImageSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = ModelImage
        fields = [
            'id',
            'image',
            'is_image_for_progress',
            'created'
        ]
