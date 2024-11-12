from django import forms
from django.core.serializers.json import DjangoJSONEncoder
from .models import Recipe, Category
import json

# Define a form for the Recipe model using Django's ModelForm
class RecipeForm(forms.ModelForm):
    ingredients = forms.CharField(
        widget=forms.Textarea(attrs={
            'placeholder': 'e.g.\nbanana\napple\nmango\nmilk\nice'
        }),
        help_text="Enter each ingredient on a new line."
    )

    class Meta:
        model = Recipe
        fields = ['title', 'description', 'ingredients', 'instructions', 'category', 'image']

    def save(self, commit=True):
        instance = super(RecipeForm, self).save(commit=False)
        # Split lines into a list and remove empty lines
        ingredients_list = [line.strip() for line in self.cleaned_data['ingredients'].splitlines() if line.strip()]
        # Convert list to JSON
        instance.ingredients = json.dumps(ingredients_list, cls=DjangoJSONEncoder)
        if commit:
            instance.save()
        return instance
            
# Define a form for searching recipes by ingredients

class IngredientSearchForm(forms.Form):
    ingredients = forms.CharField(
        label="Enter ingredients (comma-separated)",
        widget=forms.TextInput(attrs={'placeholder': 'e.g., tomato, garlic, onion'})
    )