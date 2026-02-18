from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile
from django.core.cache import cache
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer

class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', required=False)
    email = serializers.CharField(source='user.email', required=False)
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    partners = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ['username', 'email', 'first_name', 'last_name', 'cycle_length', 
                 'period_duration', 'profile_picture', 'partners', 'sex']

    def get_partners(self, obj):
        return [{
            "username": partner.user.username,
            "email": partner.user.email,
            "partner_user_id": partner.user.id
        } for partner in obj.partners.all()]

    def update(self, instance, validated_data):
        # Extract user data if present
        user_data = validated_data.pop('user', {})
        
        # Update UserProfile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Update related User fields
        user = instance.user
        for attr, value in user_data.items():
            setattr(user, attr, value)
        
        user.save()
        instance.save()
        
        return instance


class UserInvitationSerializer(serializers.Serializer):
    invitation_code = serializers.CharField(required=False, read_only=True)
    code_to_accept = serializers.CharField(required=False, write_only=True)

    def validate_code_to_accept(self, value):
        print("validate_code_to_accept")
        if value:
            user_id = cache.get(f'invitation_code_{value}')
            if not user_id:
                raise serializers.ValidationError("Invalid or expired invitation code")
            
            # Check if the invitation code belongs to the current user
            request = self.context.get('request')
            if user_id == request.user.id:
                raise serializers.ValidationError("You cannot add yourself as a partner")
                
        return value

    def create(self, validated_data):
        print("create")
        # Since we're not actually creating a model instance,
        # just return the validated data
        return validated_data

    def update(self, instance, validated_data):
        # We don't need update functionality
        pass

class UserCreateSerializer(BaseUserCreateSerializer):
    sex = serializers.ChoiceField(choices=[
        ('none', 'None'),
        ('male', 'Male'),
        ('female', 'Female')
    ], write_only=True)

    class Meta(BaseUserCreateSerializer.Meta):
        fields = tuple(list(BaseUserCreateSerializer.Meta.fields) + ['sex'])

    def validate(self, attrs):
        # Store sex separately
        self.sex = attrs.pop('sex')
        # Validate remaining user data
        return super().validate(attrs)

    def create(self, validated_data):
        # Create the user first
        user = super().create(validated_data)
        
        # Now update the profile that was created by the signal
        profile = user.userprofile
        profile.sex = self.sex
        profile.save()
        
        return user

class RemovePartnerView(serializers.Serializer):
    remove_code = serializers.CharField(required=False, allow_blank=True)

    def validate_remove_code(self, value):
        print("validate_remove_code")
        print(cache.get(f'remove_code_{value}'))
        if value:
            user_id = cache.get(f'remove_code_{value}')
            if not user_id:
                raise serializers.ValidationError("Invalid or expired invitation code")
            
            # Check if the invitation code belongs to the current user
            # request = self.context.get('request')
            # if user_id == request.user.id:
            #     raise serializers.ValidationError("You cannot add yourself as a partner")
                
        return value
