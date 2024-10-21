from django.apps import AppConfig

# Define the configuration for the 'recipes' app
class RecipesConfig(AppConfig):
    # Use 'BigAutoField' as the default field type for auto-incrementing primary keys
    default_auto_field = 'django.db.models.BigAutoField'
    
    # The name of the app this configuration applies to
    name = 'recipes'