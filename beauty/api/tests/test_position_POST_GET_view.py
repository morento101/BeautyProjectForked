"""This module is for testing position ListCreatView.

Tests for PositionListCreateView:
- SetUp method adds needed data for tests;
- Get 1 created positions;
- Post valid position;
- Customer must be authenticated;
- Start time must go before end time;
- Owner isn't allowed to post empty data.
"""

import json
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.reverse import reverse
from api.serializers.position_serializer import PositionSerializer
from api.models import Position
from api.views_api import PositionListCreateView
from .factories import (BusinessFactory,
                        CustomUserFactory,
                        GroupFactory,
                        PositionFactory)


class TestPositionListCreateView(TestCase):
    """TestCase to test PositionListCreateView."""

    def setUp(self):
        """Create business and 2 specialists."""
        self.groups = GroupFactory.groups_for_test()
        self.specialist1 = CustomUserFactory(first_name="UserSpecialist")
        self.specialist2 = CustomUserFactory(first_name="UserSpecialist2")
        self.groups.specialist.user_set.add(self.specialist1)
        self.groups.specialist.user_set.add(self.specialist2)

        self.serializer = PositionSerializer
        self.queryset = Position.objects.all()
        self.serializer = PositionSerializer
        self.view = PositionListCreateView.as_view()

        self.owner = CustomUserFactory(first_name="OwnerUser")
        self.groups.owner.user_set.add(self.owner)

        self.business = BusinessFactory(name="Hope", owner=self.owner)
        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)

        self.position_testing = PositionFactory.build(name="Wyh")
        self.position_testing = {
            "name": self.position_testing.name,
            "business": self.business.id,
            "specialist": [self.specialist1.id],
            "start_time": str(self.position_testing.start_time.time()),
            "end_time": str(self.position_testing.end_time.time()),
        }

        self.url = reverse("api:position-list")

    def test_position_get_from_valid_business(self):
        """Get 1 created position."""
        self.position = PositionFactory.create(
            business=self.business,
            specialist=[self.specialist1],
        )
        response = self.client.generic(
            method="GET",
            path=self.url,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)

    def test_position_post_list_create_view(self):
        """POST requests to ListCreateAPIView with valid data should create a new object."""
        response = self.client.generic(
            method="POST",
            path=self.url,
            data=json.dumps(self.position_testing),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)

    def test_position_post_list_create_view_no_authenticate(self):
        """POST requests to ListCreateAPIView with no authenticate shouldn't create a new object."""
        self.client.force_authenticate(user=None)
        response = self.client.generic(
            method="POST",
            path=self.url,
            data=self.position_testing,
        )
        self.assertEqual(response.status_code, 401)

    def test_position_post_list_create_view_invalid_time(self):
        """POST requests to ListCreateAPIView with invalid time shouldn't create a new object."""
        self.position_testing["end_time"] = self.position_testing["start_time"]
        response = self.client.generic(
            method="POST",
            path=self.url,
            data=json.dumps(self.position_testing),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_position_post_list_create_view_empty_data(self):
        """POST requests to ListCreateAPIView with empty data shouldn't create a new object."""
        response = self.client.generic(
            method="POST",
            path=self.url,
            data=json.dumps({}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
