from django import forms
from .models import Recipe, Category

# Define a form for the Recipe model using Django's ModelForm
class RecipeForm(forms.ModelForm):
    class Meta:
        # Specify the model the form is based on (Recipe)
        model = Recipe
        # Specify the fields from the Recipe model that will be included in the form
        fields = ['title', 'description', 'ingredients', 'instructions', 'category']

    # Custom initialization of the form to apply Bootstrap styling to all fields
    def __init__(self, *args, **kwargs):
        # Call the parent class's __init__ method to maintain default behavior
        super(RecipeForm, self).__init__(*args, **kwargs)
        # Loop through each field in the form and apply the 'form-control' class for Bootstrap styling
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'