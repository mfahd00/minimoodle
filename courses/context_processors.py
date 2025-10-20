from .models import Category

def categories(request):
    """Make categories available in all templates."""
    return {
        'categories': Category.objects.all()
    }
