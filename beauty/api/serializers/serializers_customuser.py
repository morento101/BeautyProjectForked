"""The module includes serializers for all project models."""

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.reverse import reverse

from api.models import (CustomUser, Order)

group_queryset = Group.objects.all()


class OrderUserHyperlink(serializers.HyperlinkedRelatedField):
    """Custom HyperlinkedRelatedField for user orders."""

    view_name = 'api:specialist-order-detail'
    url_user_id = 'specialist_id'

    def __init__(self, **kwargs):
        self.view_name = kwargs.pop('view_name', self.view_name)
        self.url_user_id = kwargs.pop('url_user_id', self.url_user_id)
        super().__init__(**kwargs)

    def get_url(self, obj: object, view_name: str, request: dict,
                format: str) -> str:
        """Given an object, return the URL that hyperlinks to the object.

        May raise a `NoReverseMatch` if the `view_name` and `lookup_field`
        attributes are not configured to correctly match the URL conf.

        Returns:
            url (str):  hyperlinks to the object

        """
        url_kwargs = {
            'user': getattr(obj, self.url_user_id),
            'id': obj.pk
        }
        return reverse(
            view_name, kwargs=url_kwargs, request=request, format=format
        )


class PasswordsValidation(serializers.Serializer):
    """Validator for passwords."""

    def validate(self, data: dict) -> dict:
        """Validate password and password confirmation.

        Args:
            data (dict): dictionary with data for user creation

        Returns:
            data (dict): dictionary with validated data for user creation

        """
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        if password and confirm_password:
            if password != confirm_password:
                raise serializers.ValidationError(
                    {"password": "Password confirmation does not match."}
                )
        elif any([password, confirm_password]):
            raise serializers.ValidationError(
             {"confirm_password": "Didn`t enter the password confirmation."})

        return super().validate(data)


class GroupListingField(serializers.RelatedField):
    """The custom field for user groups."""

    def to_representation(self, value: object) -> str:
        """Change representation of instance from id to name.

        Args:
            value (object): instance of group

        Returns:
            object.name (str): attribute-name of an instance

        """
        return value.name

    def to_internal_value(self, data: str) -> int:
        """Reload lookup key from id to name of the instance.

        Args:
            data (str): lookup key (instance name)

        Returns:
            id (int): instance id

        """
        return self.get_queryset().get(name=data).id


class CustomUserSerializer(PasswordsValidation,
                           serializers.HyperlinkedModelSerializer):
    """Serializer for getting all users and creating a new user."""

    url = serializers.HyperlinkedIdentityField(
        view_name='api:user-detail', lookup_field='pk'
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password', 'placeholder': 'Password'},
        validators=[validate_password]
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password',
               'placeholder': 'Confirmation Password'
               }
    )
    groups = GroupListingField(
        many=True,
        required=False,
        queryset=group_queryset
    )
    specialist_orders = OrderUserHyperlink(many=True, read_only=True)
    customer_orders = OrderUserHyperlink(
        many=True,
        read_only=True,
        url_user_id='customer_id'
    )

    class Meta:
        """Class with a model and model fields for serialization."""

        model = CustomUser
        fields = ['url', 'id', 'email', 'first_name', 'patronymic',
                  'last_name', 'phone_number', 'bio', 'rating', 'avatar',
                  'is_active', 'groups', 'specialist_orders',
                  'customer_orders', 'password', 'confirm_password']

    def create(self, validated_data: dict) -> object:
        """Create a new user using dict with data.

        Args:
            validated_data (dict): validated data for new user creation

        Returns:
            user (object): new user

        """
        confirm_password = validated_data.pop('confirm_password')
        validated_data['password'] = make_password(confirm_password)
        return super().create(validated_data)


class CustomUserDetailSerializer(PasswordsValidation,
                                 serializers.ModelSerializer):
    """Serializer to receive and update a specific user."""

    groups = GroupListingField(many=True, queryset=group_queryset)
    password = serializers.CharField(
        write_only=True,
        allow_blank=True,
        validators=[validate_password],
        style={'input_type': 'password', 'placeholder': 'New Password'}
    )
    confirm_password = serializers.CharField(
        write_only=True,
        allow_blank=True,
        help_text='Leave empty if no change needed',
        style={
            'input_type': 'password',
            'placeholder': 'Confirmation Password'
        }
    )
    specialist_orders = OrderUserHyperlink(many=True, read_only=True)
    customer_orders = OrderUserHyperlink(
        many=True,
        read_only=True,
        url_user_id='customer_id'
    )

    class Meta:
        """Class with a model and model fields for serialization."""

        model = CustomUser
        fields = ['id', 'email', 'first_name', 'patronymic', 'last_name',
                  'phone_number', 'bio', 'rating', 'avatar', 'is_active',
                  'groups', 'specialist_orders',  'customer_orders',
                  'password', 'confirm_password']

    def update(self, instance: object, validated_data: dict) -> object:
        """Update user information using dict with data.

        Args:
            instance (object): instance for changing
            validated_data (dict): validated data for updating instance

        Returns:
            user (object): instance with updated data

        """
        confirm_password = validated_data.pop('confirm_password')
        if confirm_password:
            validated_data['password'] = make_password(confirm_password)
        return super().update(instance, validated_data)


class UserOrderDetailSerializer(serializers.ModelSerializer):
    """Serializer to receive and update a specific order."""

    class Meta:
        """Class with a model and model fields for serialization."""

        model = Order
        fields = ['id', 'customer_id', 'specialist_id']
