from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Notification
from accounts.views import role_required

@login_required
def notification_list(request):
    notifications = Notification.objects.select_related('author').all().order_by('-created_at')
    return render(request, 'notifications/notification_list.html', {'notifications': notifications})

@login_required
@role_required(['ADMIN', 'EXAM_CONTROLLER', 'TEACHER'])
def notification_add(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        message = request.POST.get('message')
        
        try:
            Notification.objects.create(
                title=title,
                message=message,
                author=request.user
            )
            messages.success(request, f"Notice '{title}' published successfully.")
        except Exception as e:
            messages.error(request, f"Error publishing notice: {str(e)}")
            
    return redirect('notification_list')

@login_required
@role_required(['ADMIN', 'EXAM_CONTROLLER', 'TEACHER'])
def notification_delete(request, pk):
    notice = get_object_or_404(Notification, pk=pk)
    user_role = getattr(request.user.profile, 'role', '')
    
    # ADMIN and EXAM_CONTROLLER can delete any notice; authors can delete their own
    if user_role in ['ADMIN', 'EXAM_CONTROLLER'] or notice.author == request.user:
        title = notice.title
        notice.delete()
        messages.success(request, f"Notice '{title}' has been deleted successfully.")
    else:
        messages.error(request, "You do not have permission to delete this notice.")
        
    return redirect('notification_list')
