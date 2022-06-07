"""Module with permissions for api application."""

import logging

from django.contrib.auth.models import Group

from rest_framework import permissions


logger = logging.getLogger(__name__)


class IsAccountOwnerOrReadOnly(permissions.BasePermission):
    """IsAccountOwnerOrReadOnly permission class.

    Object-level permission to only allow owners of an object
    to edit it.
    """

    def has_object_permission(self, request, view, obj):
        """Object permission check."""
        logger.debug(f"Object {obj.id} permission check")

        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and (request.user.is_admin or (obj == request.user))


class IsAdminOrThisBusinessOwner(permissions.IsAuthenticated):
    """IsAdminOrBusinessOwner permission class.

    Object-level permission to only allow owners of an object
    or admin to review and edit it.
    """

    def has_object_permission(self, request, view, obj):
        """Verify that the current user is selected business owner or administrator."""
        logger.info(f"User {request.user} permission check")
        try:
            return request.user.is_admin or (obj.owner == request.user)
        except AttributeError:
            logger.warning(f"User {request.user} is not authorised to view this information")


class IsOrderUser(permissions.BasePermission):
    """Object-level permission to only allow users of an object to edit it."""

    def has_object_permission(self, request, view, obj):
        """Object permission check."""
        logger.debug(f"Object {obj.id} permission check")

        return obj.specialist == request.user or obj.customer == request.user


class IsPositionOwner(permissions.BasePermission):
    """IsPositionOwner permission class.

    Allows only position owners and specialist to work with it.
    """
    def has_object_permission(self, request, view, obj):
        """Object permission check."""
        logger.debug(f"Object {obj.id} permission check. Is position owner")

        if "Owner" in request.user.groups.all().values_list("name", flat=True):
            return obj.business.owner == request.user
        else:
            return False


class IsProfileOwner(permissions.IsAuthenticated):
    """Permission used in Users profile."""

    def has_object_permission(self, request, view, obj):
        """User Profile permission.

        Object-level permission to only allow users of an object to edit it, still
        it allows to view an object for non-users.
        """
        logger.info(f"{request.user} (id={request.user.id}) tried to access "
                    f"object {obj.id}, permission is checked")

        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_admin or obj == request.user


class ReadOnly(permissions.BasePermission):
    """Permission which gives access for SAFE_METHODS."""

    def has_permission(self, request, view):
        """Checks if method in SAFE_METHODS."""
        return request.method in permissions.SAFE_METHODS


class IsOwner(permissions.BasePermission):
    """Permission class which checks if current user is an owner."""

    def has_permission(self, request, view):
        """Checks if user belongs to owner group."""
        user = request.user

        if user.is_authenticated:
            try:
                user.groups.get(name="Owner")
                logger.error("User have owner permission")
                return True

            except Group.DoesNotExist:
                logger.error("Current user is not an owner")

        return False
