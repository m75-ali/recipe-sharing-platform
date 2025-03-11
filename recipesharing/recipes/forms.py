from django import forms
from .models import Recipe, Allergen

class RecipeForm(forms.ModelForm):
    allergen_free = forms.ModelMultipleChoiceField(
        queryset=Allergen.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select the allergens that this recipe contains"
    )

    ingredients = forms.CharField(
        widget=forms.Textarea(attrs={
            'placeholder': 'e.g.\nbanana\napple\nmango\nmilk\nice',
            'rows': 4  # Adjust rows for better UI
        }),
        help_text="Enter each ingredient on a new line."
    )

    class Meta:
        model = Recipe
        fields = ['title', 'description', 'ingredients', 'instructions', 'category', 'image', 'allergen_free']

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Process ingredients field: split by lines, strip unnecessary spaces
        ingredients_list = [line.strip() for line in self.cleaned_data['ingredients'].splitlines() if line.strip()]
        instance.ingredients = "\n".join(ingredients_list)

        if commit:
            instance.save()
            self.save_m2m()  # Save many-to-many relationships (allergens)

        return instance

    def clean_ingredients(self):
        ingredients = self.cleaned_data.get('ingredients', '').strip()
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
