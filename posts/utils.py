from django.core.paginator import Paginator
from django.conf import settings


def make_pages(request, post_list, posts_num=settings.POSTS_PER_PAGE):
    paginator = Paginator(post_list, posts_num)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
