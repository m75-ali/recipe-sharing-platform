from django import forms
from django.core.serializers.json import DjangoJSONEncoder
from .models import Recipe, Category, Allergen
import json


from django import forms
from .models import Recipe

# forms.py
class RecipeForm(forms.ModelForm):
    allergen_free = forms.ModelMultipleChoiceField(
        queryset=Allergen.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select the allergens that this recipe does NOT contain"
    )

class RecipeForm(forms.ModelForm):
    ingredients = forms.CharField(
        widget=forms.Textarea(attrs={
            'placeholder': 'e.g.\nbanana\napple\nmango\nmilk\nice'
        }),
        help_text="Enter each ingredient on a new line."
    )

    class Meta:
        model = Recipe
        fields = ['title', 'description', 'ingredients', 'instructions', 'category', 'image', 'allergen_free']

    def save(self, commit=True):
        # Create the instance but don't save it yet
        instance = super().save(commit=False)

        # Process the ingredients field: split by lines and strip unnecessary spaces
        ingredients_list = [
            line.strip()
            for line in self.cleaned_data['ingredients'].splitlines()
            if line.strip()
        ]
        
        # Store the ingredients as plain-text string
        instance.ingredients = "\n".join(ingredients_list)
        
        # Save the instance if commit=True
        if commit:
            instance.save()
        
        return instance

    def clean_ingredients(self):
        ingredients = self.cleaned_data.get('ingredients', '')
        if not ingredients:
            raise forms.ValidationError("Ingredients field is required.")
        return ingredients


class IngredientSearchForm(forms.Form):
    ingredients = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Enter ingredients, separated by commas.'
        })
    )