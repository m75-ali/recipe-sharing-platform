from django import forms
from .models import Recipe, Category
import json

# Define a form for the Recipe model using Django's ModelForm
class RecipeForm(forms.ModelForm):
    ingredients = forms.CharField(widget=forms.Textarea, help_text="Enter each ingredient on a new line.")

    class Meta:
        model = Recipe
        fields = ['title', 'description', 'ingredients', 'instructions', 'category']

    def save(self, commit=True):
        instance = super(RecipeForm, self).save(commit=False)
        # Split lines and store as a list
        ingredients_list = self.cleaned_data['ingredients'].splitlines()
        instance.set_ingredients(ingredients_list)
        if commit:
            instance.save()
        return instance
            
# Define a form for searching recipes by ingredients

class IngredientSearchForm(forms.Form):
    ingredients = forms.CharField(
        label="Enter ingredients (comma-separated)",
        widget=forms.TextInput(attrs={'placeholder': 'e.g., tomato, garlic, onion'})
    )