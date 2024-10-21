from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Profile model to extend the default Django User model
class Profile(models.Model):
    # One-to-one relationship with the User model, ensures each user has one profile
    user = models.OneToOneField(User, on_delete=models.CASCADE)  
    # Boolean field to track if the user has agreed to the privacy policy
    agree_to_privacy_policy = models.BooleanField(default=False)  

    # Return a string representation of the Profile, showing the associated username
    def __str__(self):
        return f'{self.user.username} Profile'


# Signal to automatically create a profile when a new user is created
@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    # Check if a new user was created
    if created:
        Profile.objects.create(user=instance)  # Create a profile for the new user


# Signal to automatically save the profile when the user is saved
@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    instance.profile.save()  # Save the user's profile when the user instance is saved