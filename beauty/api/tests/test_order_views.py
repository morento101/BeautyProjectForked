"""This module is for testing order"s views.

Tests for OrderCreateView:
- SetUp method adds needed info for tests;
- Only a logged user can create an order;
- A logged user should be able to create an order;
- Service should exist for specialist;
- Service of the order should not be empty;
- Specialist of the order should not be empty;
- Specialist should not be able to create order for himself;
- Check calling change_order_status_to_decline task when order creates.

Tests for OrderApprovingView:
- SetUp method adds needed info for tests;
- The specialist is redirected to the order detail page if he approved the order;
- The specialist is redirected to the own page if he declined the order;
- The specialist is redirected to the own page if the order token expired;
- The user is redirected to the order specialist detail page if he is not logged;
- Check calling reminder_for_customer task before start order.

Tests for OrderRetrieveCancelView:
- SetUp method adds needed info for tests;
- Only a logged user from order (customer, specialist) can retrieve an order;
- Logged order customer can retrieve an order;
- Logged order specialist can retrieve an order;
- Cancel order with valid reason by specialist;
- Cancel order with valid reason by customer;
- Cancel order with invalid reason;
- Not logged user can not cancel an order;
- Users not from order can not cancel it;
- Test an order with statuses which can not change.

Tests for CustomerOrdersViews:
- SetUp method adds needed info for tests;
- Not logged users can not rearview a customer's orders;
- Logged users can't view a customer's orders;
- Only a logged customer can rearview his own orders;
- Check count customer orders;
- Check response data for customer orders.

Tests for SpecialistOrdersViews:
- SetUp method adds needed info for tests;
- Not logged users cannot get a specialist's orders;
- Logged users, which are not specialist, can't view a specialist's orders;
- A logged owner cannot view others specialist`s orders;
- Only a logged owner of business can view his specialist orders which belong to this business;
- Only a logged specialist can get his own orders;
- Check count specialist orders for specialist;
- Check response data for specialist orders.
"""

from datetime import timedelta
from unittest.mock import patch

from django.utils import timezone
from django.conf import settings
from django.test import TestCase
from djoser.utils import encode_uid
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.reverse import reverse
from rest_framework.test import (APIClient, APIRequestFactory)
from api.serializers.order_serializers import OrderSerializer
from api.views.order_views import (OrderApprovingTokenGenerator, OrderRetrieveCancelView)
from .factories import (GroupFactory,
                        BusinessFactory,
                        CustomUserFactory,
                        PositionFactory,
                        ServiceFactory,
                        OrderFactory)
from api.models import Order
from beauty.utils import string_to_time
from api.views.schedule import get_working_day


class TestOrderCreateView(TestCase):
    """This class represents a Test case and has all the tests for OrderListCreateView."""

    working_time = {"Mon": ["08:52", "15:02"], "Tue": ["08:52", "15:02"], "Wed": ["08:52", "15:02"],
                    "Thu": ["08:52", "15:02"], "Fri": ["08:52", "15:02"], "Sat": ["08:52", "15:02"],
                    "Sun": ["08:52", "15:02"]}

    def setUp(self) -> None:
        """This method adds needed info for tests."""
        self.Serializer = OrderSerializer

        self.groups = GroupFactory.groups_for_test()
        self.specialist = CustomUserFactory(first_name="UserSpecialist")
        self.customer = CustomUserFactory(first_name="UserCustomer")
        self.position = PositionFactory(name="Position_1", working_time=self.working_time)
        self.service = ServiceFactory(name="Service_1", position=self.position)

        self.groups.specialist.user_set.add(self.specialist)
        self.groups.customer.user_set.add(self.customer)
        self.position.specialist.add(self.specialist)

        self.client = APIClient()
        self.client.force_authenticate(user=self.customer)
        working_day = timezone.now() + timedelta(days=1)
        working_hours = get_working_day(self.position, working_day)
        self.start_time = timezone.datetime.combine(working_day.date(),
                                                    string_to_time(working_hours[0]))

        self.data = [{"start_time": self.start_time,
                      "specialist": self.specialist.id,
                      "service": self.service.id}]

    def test_post_method_create_order_not_logged_user(self):
        """Only a logged user can create an order."""
        self.client.force_authenticate(user=None)
        response = self.client.post(path=reverse("api:order-create"), data=self.data)
        self.assertEqual(response.status_code, 401)

    @patch("api.tasks.change_order_status_to_decline.apply_async")
    def test_post_method_create_order_logged_user(self, change_order_status_to_decline):
        """A logged user should be able to create an order."""
        response = self.client.post(path=reverse("api:order-create"), data=self.data)
        self.assertEqual(response.status_code, 201)

    def test_post_method_create_order_service_not_exist_for_specialist(self):
        """Service should exist for specialist."""
        self.position.specialist.remove(self.specialist)
        response = self.client.post(path=reverse("api:order-create"), data=self.data)
        self.assertEqual(response.status_code, 400)

    def test_post_method_create_order_wrong_service_empty(self):
        """Service of the order should not be empty."""
        self.data[0]["service"] = ""
        response = self.client.post(path=reverse("api:order-create"), data=self.data)
        self.assertEqual(response.status_code, 400)

    def test_post_method_create_order_wrong_specialist_empty(self):
        """Specialist of the order should not be empty."""
        self.data[0]["specialist"] = ""
        response = self.client.post(path=reverse("api:order-create"), data=self.data)
        self.assertEqual(response.status_code, 400)

    def test_post_method_create_order_cant_specialist_to_himself(self):
        """Specialist should not be able to create order for himself."""
        self.client.force_authenticate(user=self.specialist)
        response = self.client.post(path=reverse("api:order-create"), data=self.data)
        self.assertEqual(response.status_code, 400)

    def test_celery_config(self):
        """Check celery config."""
        self.assertIsNotNone(settings.BROKER_URL)
        self.assertIsNotNone(settings.CELERY_RESULT_BACKEND)
        self.assertIsNotNone(settings.CELERY_ACCEPT_CONTENT)
        self.assertIn("redis", settings.BROKER_URL)

    @patch("api.tasks.change_order_status_to_decline.apply_async")
    def test_change_order_status_to_decline_called(self, mock_task):
        """Check calling change_order_status_to_decline task when order creates."""
        self.client.post(path=reverse("api:order-create"), data=self.data)
        self.assertTrue(mock_task.called)


class TestOrderApprovingView(TestCase):
    """This class represents a Test case and has all the tests for OrderApprovingView."""

    def setUp(self) -> None:
        """This method adds needed info for tests."""
        self.Serializer = OrderSerializer
        self.client = APIClient()

        self.specialist = CustomUserFactory(first_name="UserSpecialist")
        self.customer = CustomUserFactory(first_name="UserCustomer")
        self.service = ServiceFactory(name="Service_1")

        self.client.force_authenticate(user=self.customer)

        self.order = OrderFactory(specialist=self.specialist,
                                  customer=self.customer,
                                  service=self.service)

        self.token = OrderApprovingTokenGenerator().make_token(self.order)
        self.status_approved = encode_uid("approved")
        self.status_declined = encode_uid("declined")
        self.url_kwargs = {"uid": encode_uid(self.order.pk),
                           "token": self.token,
                           "status": self.status_approved}

    @patch("api.tasks.reminder_for_customer.apply_async")
    def test_get_method_get_status_approved(self, mock_reminder):
        """The specialist is redirected to the order detail page if he approved the order."""
        response = self.client.get(path=reverse("api:order-approving", kwargs=self.url_kwargs))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("api:user-order-detail",
                                               kwargs={"user": self.order.specialist.id,
                                                       "pk": self.order.id}))

    def test_get_method_get_status_declined(self):
        """The specialist is redirected to the own page if he declined the order."""
        self.url_kwargs["status"] = self.status_declined
        response = self.client.get(path=reverse("api:order-approving", kwargs=self.url_kwargs))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("api:user-detail",
                                               args=[self.order.specialist.id]))

    def test_get_method_get_status_invalid_token(self):
        """The specialist is redirected to the own page if the order token expired."""
        self.url_kwargs["token"] = "invalid"
        response = self.client.get(path=reverse("api:order-approving", kwargs=self.url_kwargs))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("api:user-detail",
                                               args=[self.order.specialist.id]))

    @patch("api.tasks.reminder_for_customer.apply_async")
    def test_get_method_not_logged_user_redirect_to_specialist(self, mock_reminder):
        """The user is redirected to the order specialist detail page if he is not logged."""
        self.client.force_authenticate(user=None)
        response = self.client.get(path=reverse("api:order-approving", kwargs=self.url_kwargs))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("api:user-order-detail",
                                               kwargs={"user": self.order.specialist.id,
                                                       "pk": self.order.id}))

    @patch("api.tasks.reminder_for_customer.apply_async")
    def test_reminder_for_customer_called(self, mock_reminder):
        """Check calling reminder_for_customer task before start order."""
        self.client.get(path=reverse("api:order-approving", kwargs=self.url_kwargs))
        self.assertTrue(mock_reminder.called)


class TestOrderRetrieveCancelView(TestCase):
    """This class represents a Test case and has all the tests for OrderRetrieveCancelView."""

    def setUp(self) -> None:
        """This method adds needed info for tests."""
        self.specialist = CustomUserFactory(first_name="UserSpecialist")
        self.customer = CustomUserFactory(first_name="UserCustomer")
        self.position = PositionFactory(name="Position_1", specialist=[self.specialist])
        self.service = ServiceFactory(name="Service_1", position=self.position)

        self.order = OrderFactory(specialist=self.specialist, customer=self.customer)

        self.specialist_order_url = reverse("api:user-order-detail",
                                            args=[self.specialist.id, self.order.id])
        self.customer_order_url = reverse("api:user-order-detail",
                                          args=[self.customer.id, self.order.id])
        self.order_url = reverse("api:order-detail", args=[self.order.id])

        self.view = OrderRetrieveCancelView.as_view()

        self.client = APIClient()

        self.client.force_authenticate(user=self.specialist)
        refresh = RefreshToken.for_user(self.specialist)
        self.client.credentials(HTTP_AUTHORIZATION=f"JWT {refresh.access_token}")

    def test_get_method_retrieve_order_not_logged_user(self):
        """Only a logged user from order (customer, specialist) can retrieve an order."""
        self.client.credentials()
        order_response = self.client.get(path=self.order_url)
        specialist_response = self.client.get(path=self.specialist_order_url)
        customer_response = self.client.get(path=self.customer_order_url)

        self.assertEqual(order_response.status_code, 302)
        self.assertEqual(specialist_response.status_code, 302)
        self.assertEqual(customer_response.status_code, 302)
        self.assertEqual(order_response.url.split("?redirect_to="),
                         [settings.LOGIN_URL, self.order_url])

    def test_get_method_retrieve_order_logged_customer(self):
        """Logged order customer can retrieve an order."""
        self.client.credentials()
        self.client.force_authenticate(user=self.customer)
        refresh = RefreshToken.for_user(self.customer)
        self.client.credentials(HTTP_AUTHORIZATION=f"JWT {refresh.access_token}")

        specialist_response = self.client.get(path=self.specialist_order_url)
        customer_response = self.client.get(path=self.customer_order_url)
        order_response = self.client.get(path=self.order_url)

        self.assertEqual(specialist_response.status_code, 200)
        self.assertEqual(customer_response.status_code, 200)
        self.assertEqual(order_response.status_code, 200)

    def test_get_method_retrieve_order_logged_specialist(self):
        """Logged order specialist can retrieve an order."""
        specialist_response = self.client.get(path=self.specialist_order_url)
        customer_response = self.client.get(path=self.customer_order_url)
        order_response = self.client.get(path=self.order_url)
        self.assertEqual(specialist_response.status_code, 200)
        self.assertEqual(customer_response.status_code, 200)
        self.assertEqual(order_response.status_code, 200)

    def test_put_method_valid_reason_specialist(self):
        """Cancel order with valid reason by specialist."""
        response = self.client.put(path=self.order_url, data={"reason": "test reason"})
        self.assertEqual(response.status_code, 302)

    def test_put_method_valid_reason_customer(self):
        """Cancel order with valid reason by customer."""
        self.client.force_authenticate(user=self.customer)
        refresh = RefreshToken.for_user(self.customer)
        self.client.credentials(HTTP_AUTHORIZATION=f"JWT {refresh.access_token}")

        response = self.client.put(path=self.order_url, data={"reason": "test reason"})
        self.assertEqual(response.status_code, 302)

    def test_put_method_invalid_reason(self):
        """Cancel order with invalid reason."""
        response = self.client.put(path=self.order_url, data={"reason": ""})
        self.assertEqual(response.status_code, 400)

    def test_put_method_not_logged_user(self):
        """Not logged user can not cancel an order."""
        response = self.client.put(path=self.order_url, data={"reason": "test reason"})
        self.assertEqual(response.status_code, 302)

    def test_put_method_not_order_user(self):
        """Users not from order can not cancel it."""
        user = CustomUserFactory()
        self.client.force_authenticate(user)
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"JWT {refresh.access_token}")

        response = self.client.put(path=self.order_url, data={"reason": "test reason"})
        self.assertEqual(response.status_code, 403)

    def test_put_method_no_cancel_status(self):
        """Test an order with statuses which can not change."""
        status = Order.StatusChoices
        doesnt_require_decline_list = (status.COMPLETED, status.CANCELLED, status.DECLINED)

        for status in doesnt_require_decline_list:
            with self.subTest(status=status):
                self.order.status = status
                self.order.save()
                response = self.client.put(path=self.order_url, data={"reason": "test reason"})
                self.assertEqual(response.status_code, 400)


class TestCustomerOrdersViews(TestCase):
    """This class represents a Test case and has all the tests for CustomerOrdersViews."""

    def setUp(self) -> None:
        """This method adds needed info for tests."""
        self.Serializer = OrderSerializer
        self.client = APIClient()
        self.order_status = Order.StatusChoices
        self.specialist = CustomUserFactory(first_name="UserSpecialist")
        self.customer = CustomUserFactory(first_name="UserCustomer")
        self.service = ServiceFactory(name="Service_1")

        self.client.force_authenticate(user=self.customer)

        self.orders = [OrderFactory(specialist=self.specialist,
                                    customer=self.customer,
                                    service=self.service,
                                    status=status) for status in self.order_status]

    def test_get_method_get_customer_orders_not_logged_user(self):
        """Not logged users can not rearview a customer's orders."""
        self.client.force_authenticate(user=None)
        response = self.client.get(
            path=reverse("api:customer-orders-list", args=[self.customer.id]),
        )
        self.assertEqual(response.status_code, 401)

    def test_get_method_get_customer_orders_logged_not_customer(self):
        """Logged users can't view a customer's orders."""
        self.client.force_authenticate(user=self.specialist)
        response = self.client.get(
            path=reverse("api:customer-orders-list", args=[self.customer.id]),
        )
        self.assertEqual(response.status_code, 403)

    def test_get_method_get_customer_orders_logged_customer(self):
        """Only a logged customer can rearview his own orders."""
        response = self.client.get(
            path=reverse("api:customer-orders-list", args=[self.customer.id]),
        )
        self.assertEqual(response.status_code, 200)

    def test_get_method_check_customer_orders_data_count(self):
        """Check count customer orders."""
        response = self.client.get(
            path=reverse("api:customer-orders-list", args=[self.customer.id]),
        )
        self.assertEqual(response.data.get("count"), len(self.orders))

    def test_get_method_check_customer_orders_data(self):
        """Check response data for customer orders."""
        factory = APIRequestFactory()
        request = factory.get("/")
        response = self.client.get(
            path=reverse("api:customer-orders-list", args=[self.customer.id]),
        )
        serializer = self.Serializer(self.orders, many=True, context={"request": request})
        self.assertEqual(response.data.get("results"), serializer.data)


class TestSpecialistOrdersViews(TestCase):
    """This class represents a Test case and has all the tests for SpecialistOrdersViews."""

    def setUp(self) -> None:
        """This method adds needed info for tests."""
        self.Serializer = OrderSerializer
        self.client = APIClient()
        self.order_status = Order.StatusChoices

        self.specialist = CustomUserFactory(first_name="UserSpecialist")
        self.customer = CustomUserFactory(first_name="UserCustomer")
        self.owner1 = CustomUserFactory(first_name="UserOwner_1")
        self.owner2 = CustomUserFactory(first_name="UserOwner_2")

        self.business1 = BusinessFactory.create(name="Business_1", owner=self.owner1)
        self.position1 = PositionFactory.create(name="Position_1",
                                                business=self.business1,
                                                specialist=[self.specialist])
        self.service1 = ServiceFactory.create(name="Service_1", position=self.position1)

        self.client.force_authenticate(user=self.specialist)

        self.orders = [OrderFactory(specialist=self.specialist,
                                    customer=self.customer,
                                    service=self.service1,
                                    status=status) for status in self.order_status]

        self.groups = GroupFactory.groups_for_test()
        self.groups.specialist.user_set.add(self.specialist)
        self.groups.customer.user_set.add(self.customer)
        self.groups.owner.user_set.add(self.owner1)
        self.groups.owner.user_set.add(self.owner2)

    def test_get_method_get_specialist_orders_not_logged_user(self):
        """Not logged users can not view a specialist's orders."""
        self.client.force_authenticate(user=None)
        response = self.client.get(
            path=reverse("api:specialist-orders-list", args=[self.specialist.id]),
        )
        self.assertEqual(response.status_code, 401)

    def test_get_method_get_specialist_orders_logged_as_not_specialist(self):
        """Logged users can't view a specialist's orders."""
        self.client.force_authenticate(user=self.customer)
        response = self.client.get(
            path=reverse("api:specialist-orders-list", args=[self.specialist.id]),
        )
        self.assertEqual(response.status_code, 403)

    def test_get_method_get_specialist_orders_logged_as_owner_of_not_own_specialist(self):
        """Logged owner cannot view other specialist's orders if this specialist is not his/her."""
        self.client.force_authenticate(user=self.owner2)
        response = self.client.get(
            path=reverse("api:specialist-orders-list", args=[self.specialist.id]),
        )
        self.assertEqual(response.status_code, 403)

    def test_get_method_get_specialist_orders_logged_as_owner_of_own_specialist(self):
        """Logged owner can view an own specialist's orders."""
        self.client.force_authenticate(user=self.owner1)
        response = self.client.get(
            path=reverse("api:specialist-orders-list", args=[self.specialist.id]),
        )
        self.assertEqual(response.status_code, 200)

    def test_get_method_get_specialist_orders_logged_as_specialist(self):
        """Only a logged specialist can view his own orders."""
        response = self.client.get(
            path=reverse("api:specialist-orders-list", args=[self.specialist.id]),
        )
        self.assertEqual(response.status_code, 200)

    def test_get_method_check_specialist_orders_data_count(self):
        """Check count specialist orders."""
        response = self.client.get(
            path=reverse("api:specialist-orders-list", args=[self.specialist.id]),
        )
        self.assertEqual(response.data.get("count"), len(self.orders))

    def test_get_method_check_specialist_orders_data(self):
        """Check response data for specialist orders."""
        factory = APIRequestFactory()
        request = factory.get("/")
        response = self.client.get(
            path=reverse("api:specialist-orders-list", args=[self.specialist.id]),
        )
        serializer = self.Serializer(self.orders, many=True, context={"request": request})
        self.assertEqual(response.data.get("results"), serializer.data)
