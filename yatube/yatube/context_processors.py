import datetime as dt

from django.contrib.auth import get_user_model

User = get_user_model()


def year(request):
    """
    Добавляет переменную с текущим годом.
    """
    return {
        'year': dt.datetime.now().year
    }

def count_user(request):
    """
        Добавляет переменную с кол-м зарег-х пользователей.
    """
    user_count = User.objects.all().count()
    return {
        'user_count': user_count
    }