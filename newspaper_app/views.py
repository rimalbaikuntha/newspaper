from datetime import timedelta

from django.contrib import messages
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.generic import DetailView, ListView, TemplateView, View

from newspaper_app.forms import ContactForm, NewsletterForm
from newspaper_app.models import Category, Post


class HomeView(ListView):
    model = Post
    template_name = "aznews/home.html"
    context_object_name = "posts"
    queryset = Post.objects.filter(
        status="active", published_at__isnull=False
    ).order_by("-published_at")[:5]

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["featured_post"] = (
            Post.objects.filter(status="active", published_at__isnull=False)
            .order_by("-views_count")
            .first()
        )
        context["featured_posts"] = Post.objects.filter(
            status="active", published_at__isnull=False
        ).order_by("-views_count")[2:5]
        one_week_ago = timezone.now() - timedelta(days=7)
        context["weekly_top_posts"] = Post.objects.filter(
            status="active",
            published_at__isnull=False,
            published_at__gte=one_week_ago,
        ).order_by("-published_at")[:7]
        return context


class PostDetailView(DetailView):
    model = Post
    template_name = "aznews/detail.html"
    context_object_name = "post"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        # get current post
        obj = self.get_object()
        # id => 3
        # 2, 1
        context["previous_post"] = (
            Post.objects.filter(
                status="active", published_at__isnull=False, id__lt=obj.id
            )
            .order_by("-id")
            .first()
        )
        # id => 3
        # 4, 5, 6, 7, 8
        context["next_post"] = (
            Post.objects.filter(
                status="active", published_at__isnull=False, id__gt=obj.id
            )
            .order_by("id")
            .first()
        )
        context["recent_posts"] = Post.objects.filter(
            status="active", published_at__isnull=False
        ).order_by("-views_count")[:5]
        return context


class PostListView(ListView):
    model = Post
    template_name = "aznews/list.html"
    context_object_name = "posts"
    queryset = Post.objects.filter(
        status="active", published_at__isnull=False
    ).order_by("-published_at")
    paginate_by = 1


class PostByCategoryView(ListView):
    model = Post
    template_name = "aznews/list.html"
    context_object_name = "posts"
    paginate_by = 1

    def get_queryset(self):
        super().get_queryset()
        queryset = Post.objects.filter(
            status="active",
            published_at__isnull=False,
            category=self.kwargs["cat_id"],
        ).order_by("-published_at")
        return queryset


class PostByTagView(ListView):
    model = Post
    template_name = "aznews/list.html"
    context_object_name = "posts"
    paginate_by = 1

    def get_queryset(self):
        super().get_queryset()
        queryset = Post.objects.filter(
            status="active",
            published_at__isnull=False,
            tag=self.kwargs["tag_id"],
        ).order_by("-published_at")
        return queryset


class AboutView(TemplateView):
    template_name = "aznews/about.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["posts"] = Post.objects.filter(
            status="active", published_at__isnull=False
        ).order_by("-published_at")[:5]
        return context


class PostSearchView(View):
    def get(self, request, *args, **kwargs):
        query = request.GET.get("query")
        post_list = Post.objects.filter(
            (Q(status="active") & Q(published_at__isnull=False))
            & (Q(title__icontains=query) | Q(content__icontains=query)),
        )
        # pagination in function based views
        page = request.GET.get("page", 1)
        paginator = Paginator(post_list, 1)
        try:
            posts = paginator.page(page)
        except PageNotAnInteger:
            posts = paginator.page(1)
        except EmptyPage:
            posts = paginator.page(paginator.num_pages)

        return render(
            request,
            "aznews/search_list.html",
            {"page_obj": posts, "query": query},
        )


class ContactView(View):
    template_name = "aznews/contact.html"
    form_class = ContactForm

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request, "Successfully submitted your query. We will contact you soon."
            )
        else:
            messages.error(request, "Cannot submit your query. Something went wrong.")

        return render(
            request,
            self.template_name,
            {"form": form},
        )


class NewsletterView(View):
    form_class = NewsletterForm

    def post(self, request, *args, **kwargs):
        is_ajax = request.headers.get("x-requested-with")
        if is_ajax == "XMLHttpRequest": # if ajax ho vane forms save gar
            form = self.form_class(request.POST)
            if form.is_valid():
                form.save()
                return JsonResponse(
                    {
                        "success": True,
                        "message": "Successfully submitted to our newsletter.",
                    }
                )
            else:
                return JsonResponse(
                    {"success": False, "message": "Something went wrong."}
                )
        else:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Cannot process. Must be an ajax request.",
                }
            )
