from django.core.exceptions import PermissionDenied
from students.models import Student
from django.shortcuts import get_object_or_404

class StudentAccessMixin:
    def dispatch(self, request, *args, **kwargs):
        student = self.get_object() if hasattr(self, 'get_object') else get_object_or_404(Student, pk=kwargs['student_id'])
        
        if not request.user.is_superuser:
            if request.user.user_type == 'teacher':
                if not student.current_class.teachers.filter(user=request.user).exists():
                    raise PermissionDenied
            elif request.user.user_type == 'parent':
                if not student.parents.filter(user=request.user).exists():
                    raise PermissionDenied
            elif request.user.user_type == 'student' and request.user.student != student:
                raise PermissionDenied
                
        return super().dispatch(request, *args, **kwargs)