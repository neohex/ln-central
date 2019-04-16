# Create your views here.
from django.views.generic import DetailView, ListView, TemplateView, UpdateView, View
from .models import Blog, BlogPost
from django.conf import settings
from django.db.models import Max, Count


class BlogPostList(ListView):
    template_name = "planet/planet_entries.html"
    paginate_by = 25
    model = BlogPost
    context_object_name = 'blogposts'

    def get_queryset(self):
        query = super(BlogPostList, self).get_queryset()
        return query.select_related("blog").order_by("-creation_date")

    def get_context_data(self, **kwargs):
        get = self.request.GET.get
        self.topic = 'planet'
        context = super(BlogPostList, self).get_context_data(**kwargs)
        context['page_title'] = "Planet"
        context['topic'] = self.topic
        context['limit'] = get('limit', '')
        context['q'] = get('q', '')
        context['sort'] = get('sort', '')

        # Sort blog posts by latest insert time
        blogs = Blog.objects.all().annotate(updated_date=Max("blogpost__creation_date"),
                                            count=Count("blogpost__id")).order_by("-updated_date", "-list_order")
        context['blogs'] = blogs

        return context
