from .models import Category , Enrollment, Announcement

def categories(request):
    """Make categories available in all templates."""
    return {
        'categories': Category.objects.all()
    }

