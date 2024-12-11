from django import forms
from django.core.serializers.json import DjangoJSONEncoder
from .models import Recipe, Category
import json

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
        try:
            ingredients_list = [
                line.strip()
                for line in self.cleaned_data['ingredients'].splitlines()
                if line.strip()
            ]
            instance.ingredients = json.dumps(ingredients_list, cls=DjangoJSONEncoder)
        except Exception as e:
            raise forms.ValidationError(f"Error processing ingredients: {e}")
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