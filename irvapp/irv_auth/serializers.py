from django.contrib.auth import get_user_model
from rest_framework import serializers


User = get_user_model()


class LoginRequestSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(
        trim_whitespace=False,
        write_only=True,
        style={'input_type': 'password'},
    )


class RegistrationRequestSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(
        trim_whitespace=False,
        write_only=True,
        style={'input_type': 'password'},
    )


class CurrentUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']
