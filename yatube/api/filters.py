import django_filters as filters

from posts.models import Post


class PostFilter(filters.FilterSet):
    author = filters.CharFilter(
        field_name='author__username', lookup_expr='exact'
    )
    group = filters.CharFilter(
        field_name='group__slug', lookup_expr='exact'
    )

    class Meta:
        model = Post
        fields = ('author', 'group')
