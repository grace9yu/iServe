from core.models import Notification

def notifications_processor(request):
    if request.user.is_authenticated:
        # Get latest 5 unread or recent notifications
        recent_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        return {
            'recent_notifications': recent_notifications,
            'unread_notifications_count': unread_count,
        }
    return {
        'recent_notifications': [],
        'unread_notifications_count': 0,
    }
