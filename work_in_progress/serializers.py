from rest_framework import serializers, fields
from rest_framework.utils import html

from .models import Model, UserModelStatus, ModelGroup, KillTeam, BSUnit, BSCategory, ModelProgress, ModelImage


class UserModelGroupSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)

    class Meta:
        model = ModelGroup
        fields = ['id', 'name']

    def create(self, validated_data):
        record = ModelGroup(**validated_data)
        record.user = self.context['request'].user
        record.save()
        return record


class UserModelGroupIdPKField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        return ModelGroup.objects.filter(user=self.context['request'].user)


class UserModelStatusIdPKField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        return UserModelStatus.objects.filter(user=self.context['request'].user)


class ModelPKField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        return Model.objects.filter(user=self.context['request'].user)


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
    id = serializers.IntegerField(read_only=True)

    class Meta:
        model = UserModelStatus
        fields = ['id', 'name', 'order', 'previous', 'next', 'is_initial', 'is_final', 'transition_title']

    def create(self, validated_data):
        request = self.context['request']
        user = request.user
        record = UserModelStatus(**validated_data)
        record.user = user
        record.save()
        return record

    def validate_previous(self, value):
        if value is None:
            return value
        if value.user != self.context['request'].user:
            raise serializers.ValidationError("Предыдущий статус относится к другому пользователю")
        return value

    def validate_next(self, value):
        if value is None:
            return value
        if value.user != self.context['request'].user:
            raise serializers.ValidationError("Следующий статус относится к другому пользователю")
        return value


class ModelSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    user_status = UserModelStatusSerializer(read_only=True)
    groups = UserModelGroupSerializer(many=True, read_only=True)
    battlescribe_unit = BSUnitSerializer(read_only=True)
    kill_team = KillTeamSerializer(read_only=True)

    hours_spent = serializers.FloatField(read_only=True, source='get_hours_spent')
    get_last_image_url = serializers.CharField(read_only=True)

    groups_id = UserModelGroupIdPKField(many=True, write_only=True)
    user_status_id = UserModelStatusIdPKField(write_only=True)
    kill_team_id = serializers.PrimaryKeyRelatedField(required=False, allow_null=True, write_only=True, queryset=KillTeam.objects.all())
    battlescribe_unit_id = serializers.PrimaryKeyRelatedField(required=False, allow_null=True, write_only=True, queryset=BSUnit.objects.all())

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
            'user_status_id',
            'groups',
            'groups_id',
            'battlescribe_unit',
            'battlescribe_unit_id',
            'kill_team',
            'kill_team_id',
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

    def validate_user_status_id(self, value):
        if self.context['request'].user != value.user:
            raise serializers.ValidationError("Нельзя использовать статус другого пользователя")
        return value

    def create(self, validated_data):
        data = validated_data.copy()
        data['user'] = self.context['request'].user
        groups = []
        if 'groups_id' in data:
            groups = data.pop('groups_id')
        if 'user_status_id' in data:
            data['user_status'] = data.pop('user_status_id')
        if 'kill_team_id' in data:
            data['kill_team'] = data.pop('kill_team_id')
        if 'battlescribe_unit_id' in data:
            data['battlescribe_unit'] = data.pop('battlescribe_unit_id')
        model = Model(**data)
        model.save()
        # чтобы сохранить м2м надо сперва сохранить объект
        model.groups.set(groups)
        model.save()
        return model

    def update(self, instance: Model, validated_data):
        data = validated_data.copy()
        groups = []
        if 'groups_id' in data:
            groups = data.pop('groups_id')
        if 'user_status_id' in data:
            data['user_status'] = data.pop('user_status_id')
        if 'kill_team_id' in data:
            data['kill_team'] = data.pop('kill_team_id')
        if 'battlescribe_unit_id' in data:
            data['battlescribe_unit'] = data.pop('battlescribe_unit_id')

        for attr, value in data.items():
            setattr(instance, attr, value)
        instance.groups.set(groups)
        instance.save()
        return instance


class ModelProgressSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    user_status = UserModelStatusSerializer(read_only=True)
    get_last_image_url = serializers.CharField(read_only=True)
    description = serializers.CharField(required=False, allow_blank=True)
    model_id = ModelPKField(write_only=True)
    user_status_id = UserModelStatusIdPKField(write_only=True)

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
            'model_id',
            'user_status_id',
        ]

    def create(self, validated_data):
        data = validated_data.copy()
        if 'user_status_id' in data:
            data['user_status'] = data.pop('user_status_id')
        if 'model_id' in data:
            data['model'] = data.pop('model_id')
        record = ModelProgress(**data)
        record.save()
        return record

    def update(self, instance, validated_data):
        data = validated_data.copy()
        if 'user_status_id' in data:
            data['user_status'] = data.pop('user_status_id')
        if 'model_id' in data:
            data['model'] = data.pop('model_id')
        for attr, value in data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class ModelImageSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField()
    image = serializers.CharField(source="image.url")

    class Meta:
        model = ModelImage
        fields = [
            'id',
            'image',
            'is_image_for_progress',
            'created'
        ]
