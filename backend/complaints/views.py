"""
API Views for the Smart Complaint Management System

Endpoints:
- /api/departments/        → list, create departments
- /api/departments/<id>/   → retrieve, update, delete department
- /api/staff/              → list, create staff
- /api/staff/<id>/         → retrieve, update, delete staff
- /api/complaints/         → list all complaints (with filters)
- /api/complaints/create/  → create new complaint
- /api/complaints/<id>/    → complaint detail
- /api/complaints/<id>/status/ → update status only
- /api/complaints/<id>/track/  → track complaint timeline
- /api/assignments/        → list, create assignments
- /api/assignments/<id>/   → retrieve, update, delete assignment
- /api/stats/              → dashboard statistics
"""

from django.db.models import Count, Q

from rest_framework import generics, status  # type: ignore[import-not-found]
from rest_framework.views import APIView  # type: ignore[import-not-found]
from rest_framework.response import Response  # type: ignore[import-not-found]

from .models import Department, Staff, Complaint, ComplaintAssignment
from .serializers import (
    DepartmentSerializer,
    StaffSerializer,
    ComplaintListSerializer,
    ComplaintDetailSerializer,
    ComplaintCreateSerializer,
    ComplaintStatusUpdateSerializer,
    ComplaintAssignmentSerializer,
)
from .filters import ComplaintFilter


# ═══════════════════════════════════════════════
#  DEPARTMENT VIEWS
# ═══════════════════════════════════════════════

class DepartmentListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/departments/  → List all departments
    POST /api/departments/  → Create a new department
    """
    queryset         = Department.objects.all()
    serializer_class = DepartmentSerializer


class DepartmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/departments/<id>/  → Get department details
    PUT    /api/departments/<id>/  → Update department
    PATCH  /api/departments/<id>/  → Partial update
    DELETE /api/departments/<id>/  → Delete department
    """
    queryset         = Department.objects.all()
    serializer_class = DepartmentSerializer


# ═══════════════════════════════════════════════
#  STAFF VIEWS
# ═══════════════════════════════════════════════

class StaffListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/staff/  → List all staff
    POST /api/staff/  → Add new staff member
    """
    queryset         = Staff.objects.select_related('department').all()
    serializer_class = StaffSerializer
    search_fields    = ['name', 'email']
    filterset_fields = ['department', 'is_active']


class StaffDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/staff/<id>/  → Get staff details
    PUT    /api/staff/<id>/  → Update staff
    DELETE /api/staff/<id>/  → Remove staff
    """
    queryset         = Staff.objects.select_related('department').all()
    serializer_class = StaffSerializer


# ═══════════════════════════════════════════════
#  COMPLAINT VIEWS
# ═══════════════════════════════════════════════

class ComplaintListView(generics.ListAPIView):
    """
    GET /api/complaints/
    Supports filters: ?status=Open&priority=High&department=2
    Supports search:  ?search=water leak
    Supports order:   ?ordering=-created_at
    """
    queryset         = Complaint.objects.select_related('department').all()
    serializer_class = ComplaintListSerializer
    filterset_class  = ComplaintFilter
    search_fields    = ['title', 'description', 'created_by']
    ordering_fields  = ['created_at', 'priority', 'status']


class ComplaintCreateView(generics.CreateAPIView):
    """
    POST /api/complaints/create/
    Creates a new complaint. Priority is auto-set from description keywords.
    """
    queryset         = Complaint.objects.all()
    serializer_class = ComplaintCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        complaint = serializer.save()

        # Return full detail after creation
        detail_serializer = ComplaintDetailSerializer(complaint)
        return Response(
            {
                'message'  : 'Complaint submitted successfully!',
                'complaint': detail_serializer.data
            },
            status=status.HTTP_201_CREATED
        )


class ComplaintDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/complaints/<id>/  → Full complaint detail with assignments
    PUT    /api/complaints/<id>/  → Full update
    PATCH  /api/complaints/<id>/  → Partial update
    DELETE /api/complaints/<id>/  → Delete complaint
    """
    queryset = Complaint.objects.prefetch_related(
        'assignments__staff'
    ).select_related('department')

    def get_serializer_class(self):
        """Use detail serializer for GET, create serializer for write."""
        if self.request.method == 'GET':
            return ComplaintDetailSerializer
        return ComplaintCreateSerializer


class ComplaintStatusUpdateView(generics.UpdateAPIView):
    """
    PATCH /api/complaints/<id>/status/
    Updates only the status field of a complaint.
    Example body: {"status": "Resolved"}
    """
    queryset         = Complaint.objects.all()
    serializer_class = ComplaintStatusUpdateSerializer

    def update(self, request, *args, **kwargs):
        instance   = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'message': f'Status updated to "{instance.status}" successfully.',
            'id'     : instance.id,
            'status' : instance.status
        })


class ComplaintTrackView(APIView):
    """
    GET /api/complaints/<id>/track/
    Returns a timeline of the complaint from creation to current state.
    """

    def get(self, request, pk):
        try:
            complaint   = Complaint.objects.prefetch_related('assignments__staff').get(pk=pk)
        except Complaint.DoesNotExist:
            return Response({'error': 'Complaint not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Build a timeline list
        timeline = [
            {
                'event'    : 'Complaint Submitted',
                'detail'   : f'Raised by {complaint.created_by}',
                'timestamp': complaint.created_at,
                'icon'     : 'submitted'
            }
        ]

        # Add each assignment event to timeline
        for assignment in complaint.assignments.all():
            timeline.append({
                'event'    : f'Assigned to {assignment.staff.name}',
                'detail'   : assignment.resolution_notes or 'Working on it...',
                'timestamp': assignment.assigned_at,
                'icon'     : 'assigned'
            })

            if assignment.is_resolved:
                timeline.append({
                    'event'    : 'Marked Resolved',
                    'detail'   : f'Resolved by {assignment.staff.name}',
                    'timestamp': assignment.assigned_at,
                    'icon'     : 'resolved'
                })

        return Response({
            'complaint_id'  : complaint.id,
            'title'         : complaint.title,
            'current_status': complaint.status,
            'priority'      : complaint.priority,
            'timeline'      : timeline
        })


# ═══════════════════════════════════════════════
#  ASSIGNMENT VIEWS
# ═══════════════════════════════════════════════

class AssignmentListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/assignments/  → List all assignments
    POST /api/assignments/  → Assign a complaint to staff
    """
    queryset         = ComplaintAssignment.objects.select_related('complaint', 'staff').all()
    serializer_class = ComplaintAssignmentSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        assignment = serializer.save()

        # Auto-update complaint status to "In Progress"
        complaint        = assignment.complaint
        complaint.status = Complaint.STATUS_IN_PROGRESS
        complaint.save()

        return Response(
            {
                'message'   : f'Complaint assigned to {assignment.staff.name} successfully!',
                'assignment': serializer.data
            },
            status=status.HTTP_201_CREATED
        )


class AssignmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/assignments/<id>/  → Assignment detail
    PATCH  /api/assignments/<id>/  → Update resolution notes / mark resolved
    DELETE /api/assignments/<id>/  → Remove assignment
    """
    queryset         = ComplaintAssignment.objects.all()
    serializer_class = ComplaintAssignmentSerializer


# ═══════════════════════════════════════════════
#  DASHBOARD STATS VIEW
# ═══════════════════════════════════════════════

class DashboardStatsView(APIView):
    """
    GET /api/stats/
    Returns key metrics for the dashboard.
    """

    def get(self, request):
        total_complaints = Complaint.objects.count()

        # Count by status
        status_counts = Complaint.objects.values('status').annotate(count=Count('id'))
        status_map    = {item['status']: item['count'] for item in status_counts}

        # Count by priority
        priority_counts = Complaint.objects.values('priority').annotate(count=Count('id'))
        priority_map    = {item['priority']: item['count'] for item in priority_counts}

        # Count by department
        dept_stats = Department.objects.annotate(
            total=Count('complaints'),
            open=Count('complaints', filter=Q(complaints__status='Open'))
        ).values('name', 'total', 'open')

        # Recent complaints
        recent = Complaint.objects.order_by('-created_at')[:5].values(
            'id', 'title', 'status', 'priority', 'created_at'
        )

        return Response({
            'overview': {
                'total_complaints': total_complaints,
                'total_staff'     : Staff.objects.filter(is_active=True).count(),
                'total_departments': Department.objects.count(),
                'resolved'        : status_map.get('Resolved', 0),
            },
            'by_status'  : status_map,
            'by_priority': priority_map,
            'by_department': list(dept_stats),
            'recent_complaints': list(recent),
        })