from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import UserProfile
from .serializers import UserProfileSerializer , UserInvitationSerializer, RemovePartnerView
from django.core.cache import cache
import random

class UserProfileView(generics.RetrieveUpdateAPIView):
    """View to retrieve and update the user profile."""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Retrieve the profile of the logged-in user
        return self.request.user.userprofile

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response(serializer.data)
    
class UserInvitationView(generics.ListCreateAPIView):
    """View to handle user invitation codes.
    
    GET: View current invitation code if exists
    POST: Generate new code or accept existing code
    """
    serializer_class = UserInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]
    INVITATION_EXPIRE_SECONDS = 24 * 60 * 60

    def get_queryset(self):
        # This is needed for ListCreateAPIView but we'll override get method
        return None

    def get(self, request, *args, **kwargs):
        # Check for user's invitation code using a specific key
        invitation_key = f'user_{request.user.id}_invitation'
        code = cache.get(invitation_key)
        
        if code:
            return Response({
                'invitation_code': code,
                'expires_in': cache.ttl(invitation_key) if hasattr(cache, 'ttl') else None
            })
        
        return Response({
            'invitation_code': None,
            'message': 'No active invitation code'
        })

    def generate_invitation_code(self):
        print("start generate_invitation_code")
        while True:
            code = str(random.randint(10000, 99999))
            # Check if code is already in use
            print("code is:", code)

            if not cache.get(f'invitation_code_{code}'):
                return code
            






    def create(self, request, *args, **kwargs):
            serializer = self.get_serializer(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)

            current_profile = request.user.userprofile

            # 🔒 Check if user already has a partner
            if current_profile.partners.exists():
                return Response({
                    "error": "You already have a partner. Please remove your current partner before adding a new one.",
                    "current_partner": current_profile.partners.first().user.username
                }, status=status.HTTP_400_BAD_REQUEST)

            code_to_accept = serializer.validated_data.get('code_to_accept')

            if code_to_accept:  # ✅ Accept invitation
                partner_user_id = cache.get(f'invitation_code_{code_to_accept}')
                if not partner_user_id:
                    return Response({"error": "Invalid or expired invitation code"}, status=status.HTTP_400_BAD_REQUEST)

                if partner_user_id == request.user.id:
                    return Response({"error": "You cannot add yourself as a partner"}, status=status.HTTP_400_BAD_REQUEST)

                partner_profile = UserProfile.objects.get(user_id=partner_user_id)

                if partner_profile.partners.exists():
                    return Response({"error": "The user who generated this code already has a partner"}, status=status.HTTP_400_BAD_REQUEST)

                # Link both users
                current_profile.partners.add(partner_profile)
                partner_profile.partners.add(current_profile)

                # Invalidate used code
                cache.delete(f'invitation_code_{code_to_accept}')
                cache.delete(f'user_{partner_user_id}_invitation')

                return Response({
                    "message": "Invitation code accepted successfully",
                    "partner": partner_profile.user.username
                }, status=status.HTTP_200_OK)

            else:  # ✅ Generate new invitation code
                invitation_code = self.generate_invitation_code()
                user_id = request.user.id

                cache.set(f'invitation_code_{invitation_code}', user_id, timeout=self.INVITATION_EXPIRE_SECONDS)
                cache.set(f'user_{user_id}_invitation', invitation_code, timeout=self.INVITATION_EXPIRE_SECONDS)

                return Response({
                    "invitation_code": invitation_code,
                    "expires_in": self.INVITATION_EXPIRE_SECONDS
                }, status=status.HTTP_201_CREATED)


class RemovePartherView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RemovePartnerView
    INVITATION_EXPIRE_SECONDS = 24 * 60 * 60

    def generate_remove_code(self):
        while True:
            code = str(random.randint(10000,99999))
            print ("code is:", code)
            if not cache.get(f'remove_code_{code}'):
                return code
            
    def post(self,request, *arqs, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        current_profile = request.user.userprofile
        print("current_profile",current_profile)
        if not current_profile.partners.exists():
            return Response(
                {
                    "error":"You don't have a partner to remove."
                }, status=status.HTTP_400_BAD_REQUEST
            )
        remove_code = serializer.validated_data.get('remove_code')
        if remove_code:
            print("hello")
            partner_profile = current_profile.partners.first()
            print("partner_profile :",partner_profile)

            current_profile.partners.remove(partner_profile)
            partner_profile.partners.remove(current_profile)

            return Response({
                "message": f"Partner '{partner_profile.user.username}' removed successfully."
            }, status=status.HTTP_200_OK)
        else:
            print("bye")
            remove_code = self.generate_remove_code()
            user_id = request.user.id

            cache.set(f'remove_code_{remove_code}', user_id, timeout=self.INVITATION_EXPIRE_SECONDS)
            cache.set(f'user_{user_id}_remove', remove_code, timeout=self.INVITATION_EXPIRE_SECONDS)
            return Response({
                "remove_code": remove_code,
                "expires_in": self.INVITATION_EXPIRE_SECONDS
            }, status=status.HTTP_201_CREATED)























    # def creat(self, serializer):
    #     print("perform_create")
    #     current_profile = self.request.user.userprofile
        
    #     # Check if user already has a partner
    #     if current_profile.partners.exists():
    #         return Response({
    #             "error": "You already have a partner. Please remove your current partner before adding a new one.",
    #             "current_partner": current_profile.partners.first().user.username
    #         }, status=status.HTTP_400_BAD_REQUEST)

    #     code_to_accept = serializer.validated_data.get('code_to_accept')
        
    #     if code_to_accept:
    #         # Add debug logging
    #         print(f"Checking invitation code: {code_to_accept}")
    #         partner_user_id = cache.get(f'invitation_code_{code_to_accept}')
    #         print(f"Found partner_user_id: {partner_user_id}")
            
    #         # Check if the invitation code belongs to the current user
    #         if partner_user_id == self.request.user.id:
    #             return Response({
    #                 "error": "You cannot add yourself as a partner"
    #             }, status=status.HTTP_400_BAD_REQUEST)
                
    #         if partner_user_id:
    #             partner_profile = UserProfile.objects.get(user_id=partner_user_id)
                
    #             # Check if partner already has a partner
    #             if partner_profile.partners.exists():
    #                 return Response({
    #                     "error": "The user who generated this code already has a partner"
    #                 }, status=status.HTTP_400_BAD_REQUEST)
                
    #             # Add as partners (both ways)
    #             current_profile.partners.add(partner_profile)
    #             partner_profile.partners.add(current_profile)
                
    #             # Delete the used invitation code
    #             cache.delete(f'invitation_code_{code_to_accept}')
    #             cache.delete(f'user_{partner_user_id}_invitation')
                
    #             serializer.save(invitation_code=None)
                
    #             return Response({
    #                 "message": "Invitation code accepted successfully",
    #                 "partner": partner_profile.user.username
    #             }, status=status.HTTP_200_OK)
    #     else:
    #         # Generate new invitation code
    #         invitation_code = self.generate_invitation_code()
    #         user_id = self.request.user.id
            
    #         # Add debug logging
    #         print(f"Generated new code: {invitation_code} for user: {user_id}")
            
    #         # Store the code with both keys
    #         cache.set(
    #             f'invitation_code_{invitation_code}',
    #             user_id,
    #             timeout=self.INVITATION_EXPIRE_SECONDS,
    #         )
    #         cache.set(
    #             f'user_{user_id}_invitation',
    #             invitation_code,
    #             timeout=self.INVITATION_EXPIRE_SECONDS,
    #         )
            
    #         # Verify the values were stored
    #         print(f"Verification - invitation_code_{invitation_code}:", 
    #               cache.get(f'invitation_code_{invitation_code}'))
    #         print(f"Verification - user_{user_id}_invitation:", 
    #               cache.get(f'user_{user_id}_invitation'))
            
    #         serializer.save(invitation_code=invitation_code)
