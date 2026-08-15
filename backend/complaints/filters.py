"""
Custom filters for complaints.
These allow API consumers to filter: ?status=Open&priority=High&department=1
"""

try:
    import django_filters  # type: ignore[import-not-found]
except ImportError:
    django_filters = None  # type: ignore[assignment]

from .models import Complaint  # type: ignore[import]


class ComplaintFilter(django_filters.FilterSet):
    """
    Filter complaints by:
    - status  : ?status=Open
    - priority: ?priority=High
    - department: ?department=1
    - created_by: ?created_by=John
    - date range: ?created_after=2024-01-01&created_before=2024-12-31
    """

    created_after  = django_filters.DateFilter(field_name='created_at', lookup_expr='date__gte')
    created_before = django_filters.DateFilter(field_name='created_at', lookup_expr='date__lte')

    class Meta:
        model  = Complaint
        fields = {
            'status'     : ['exact'],
            'priority'   : ['exact'],
            'department' : ['exact'],
            'created_by' : ['exact', 'icontains'],
        }