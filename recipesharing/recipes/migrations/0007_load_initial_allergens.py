

from django.db import migrations

def create_initial_allergens(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    Allergen = apps.get_model('recipes', 'Allergen')  # replace 'recipes' with your actual app name
    
    allergens = [
        'Milk',
        'Eggs',
        'Fish',
        'Shellfish',
        'Tree nuts',
        'Peanuts',
        'Wheat',
        'Soybeans',
        'Sesame'
    ]
    
    for allergen in allergens:
        Allergen.objects.create(name=allergen)

def remove_initial_allergens(apps, schema_editor):
    # This is the reverse migration if needed
    Allergen = apps.get_model('recipes', 'Allergen')
    Allergen.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('recipes', '0006_allergen_alter_recipe_ingredients_and_more'),  # replace with your previous migration
    ]

    operations = [
        migrations.RunPython(create_initial_allergens, remove_initial_allergens),
    ]