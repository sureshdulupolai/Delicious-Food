from django.shortcuts import redirect, render
from .models import SystemErrorLog
import traceback
import sys

class ErrorLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        # Capture raw exception info
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))

        # Log to DB
        SystemErrorLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            path=request.path,
            method=request.method,
            error_message=str(exception),
            traceback=tb_str,
            status_code=500,
            resolved=False
        )

        # Return friendly warning page
        return render(request, 'warning.html', status=500)


class RoleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        
        # Security: Customers cannot open /admin or /dev/*
        if path.startswith('/admin/') or path.startswith('/dev/'):
            if not request.user.is_authenticated:
                 return redirect('login')
            
            # Must be staff/developer
            if not request.user.is_staff:
                # Redirect to home or show forbidden (404 to hide)
                return render(request, '404.html', status=404)

        response = self.get_response(request)
        return response
