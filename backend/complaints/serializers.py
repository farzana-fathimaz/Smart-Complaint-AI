"""
Serializers convert Django model instances to JSON and back.
Think of them as the bridge between your database and the API response.
"""

from rest_framework import serializers
from .models import Department, Staff, Complaint, ComplaintAssignment


class DepartmentSerializer(serializers.ModelSerializer):
    """Serializer for Department model."""

    # Count how many complaints belong to this department
    total_complaints = serializers.SerializerMethodField()
    total_staff      = serializers.SerializerMethodField()

    class Meta:
        model  = Department
        fields = ['id', 'name', 'description', 'total_complaints', 'total_staff', 'created_at']

    def get_total_complaints(self, obj):
        """Returns total complaint count for this department."""
        return obj.complaints.count()

    def get_total_staff(self, obj):
        """Returns total staff count for this department."""
        return obj.staff_members.count()


class StaffSerializer(serializers.ModelSerializer):
    """Serializer for Staff model — includes department name."""

    department_name = serializers.CharField(source='department.name', read_only=True)

    class Meta:
        model  = Staff
        fields = [
            'id', 'name', 'email', 'phone',
            'department', 'department_name',
            'is_active', 'joined_at'
        ]


class ComplaintAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for assignment — includes staff details."""

    staff_name  = serializers.CharField(source='staff.name', read_only=True)
    staff_email = serializers.CharField(source='staff.email', read_only=True)

    class Meta:
        model  = ComplaintAssignment
        fields = [
            'id', 'complaint', 'staff', 'staff_name', 'staff_email',
            'assigned_at', 'resolution_notes', 'is_resolved'
        ]


class ComplaintListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer used when listing many complaints.
    Avoids heavy nested data for performance.
    """
    department_name = serializers.CharField(source='department.name', read_only=True)

    class Meta:
        model  = Complaint
        fields = [
            'id', 'title', 'department', 'department_name',
            'status', 'priority', 'created_by', 'created_at'
        ]


class ComplaintDetailSerializer(serializers.ModelSerializer):
    """
    Full serializer with nested assignments — used for single complaint detail view.
    """
    department_name = serializers.CharField(source='department.name', read_only=True)
    assignments     = ComplaintAssignmentSerializer(many=True, read_only=True)

    class Meta:
        model  = Complaint
        fields = [
            'id', 'title', 'description',
            'department', 'department_name',
            'status', 'priority',
            'created_by', 'created_at', 'updated_at',
            'assignments'
        ]


class ComplaintCreateSerializer(serializers.ModelSerializer):
    """Used when creating a new complaint (POST request)."""

    class Meta:
        model  = Complaint
        fields = ['title', 'description', 'department', 'priority', 'created_by']

    def validate_title(self, value):
        """Ensure title is at least 10 characters."""
        if len(value) < 10:
            raise serializers.ValidationError("Title must be at least 10 characters.")
        return value

    def validate_description(self, value):
        """Ensure description is at least 20 characters."""
        if len(value) < 20:
            raise serializers.ValidationError("Description must be at least 20 characters.")
        return value


class ComplaintStatusUpdateSerializer(serializers.ModelSerializer):
    """Used specifically for updating just the status of a complaint."""

    class Meta:
        model  = Complaint
        fields = ['status']