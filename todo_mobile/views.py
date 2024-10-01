from rest_framework import viewsets, permissions

from .models import Task, CheckList
from .serializers import TaskSerializer, ChecklistSerializer


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.AllowAny]


class CheckListViewSet(viewsets.ModelViewSet):
    serializer_class = ChecklistSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        if 'task_id' not in self.request.query_params:
            return CheckList.objects.none()
        return CheckList.objects.filter(task_id=self.request.query_params['task_id'])
