from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'created_at', 'is_staff', 'is_superuser')
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, validators=[validate_password])

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def validate_email(self, value):
        normalized_email = value.lower()

        if User.objects.filter(email__iexact=normalized_email).exists():
            raise serializers.ValidationError('A user with this email already exists.')

        return normalized_email

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        user = authenticate(username=username, password=password)

        if user is None:
            try:
                matched_user = User.objects.get(email__iexact=username)
            except User.DoesNotExist:
                matched_user = None

            if matched_user is not None:
                user = authenticate(username=matched_user.username, password=password)

        if user is None:
            raise serializers.ValidationError({'detail': 'Invalid username/email or password.'})

        if not user.is_active:
            raise serializers.ValidationError({'detail': 'This account is inactive.'})

        attrs['user'] = user
        return attrs
