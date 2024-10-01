from rest_framework import serializers

from .models import Task, CheckList, CheckListItem


class TaskSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'name', 'related_place', 'address', 'activity']


class CheckListItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CheckListItem
        fields = ['id', 'work', 'unit', 'count']


class ChecklistSerializer(serializers.ModelSerializer):
    items = CheckListItemSerializer(many=True, read_only=True)

    class Meta:
        model = CheckList
        fields = ['id', 'task_id', 'items']
