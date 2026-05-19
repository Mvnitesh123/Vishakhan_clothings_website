from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from fashion.models import User

class AutoLinkSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # If this social account is already linked to a user, do nothing
        if sociallogin.is_existing:
            return
            
        # Get the email from the social login
        email = sociallogin.email_addresses[0].email if sociallogin.email_addresses else None
        if not email:
            return
            
        # Search for an existing user with this exact email
        try:
            user = User.objects.get(email__iexact=email)
            # Connect this social account to the existing local user account
            sociallogin.connect(request, user)
        except User.DoesNotExist:
            pass
