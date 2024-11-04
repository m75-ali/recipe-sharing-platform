from django.test import TestCase
from django.contrib.auth.models import User
from .models import Recipe, Category, Rating, find_recipes_by_ingredients
from django.urls import reverse
import json

class RecipeModelTest(TestCase):
    
    def setUp(self):
        # Create a test user and a category
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.category = Category.objects.create(name="Test Category")

    def test_recipe_str_method(self):
        recipe = Recipe.objects.create(
            title="Test Recipe",
            description="Test description",
            ingredients=json.dumps(["Test ingredient"]),
            instructions="Test instructions",
            category=self.category,
            creator=self.user
        )
        self.assertEqual(str(recipe), "Test Recipe")

    def test_recipe_creation(self):
        recipe_count = Recipe.objects.count()
        Recipe.objects.create(
            title="New Recipe",
            description="Description for new recipe",
            ingredients=json.dumps(["Ingredient"]),
            instructions="Instructions for new recipe",
            category=self.category,
            creator=self.user
        )
        self.assertEqual(Recipe.objects.count(), recipe_count + 1)


class RecipeViewTest(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.other_user = User.objects.create_user(username="otheruser", password="otherpass")
        self.category = Category.objects.create(name="Test Category")
        self.recipe = Recipe.objects.create(
            title="Test Recipe",
            description="Test description",
            ingredients=json.dumps(["Test ingredient"]),
            instructions="Test instructions",
            category=self.category,
            creator=self.user
        )
        self.client.login(username="testuser", password="testpass")

    def test_recipe_list_view(self):
        response = self.client.get(reverse("recipe_index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Recipe")

    def test_recipe_detail_view(self):
        response = self.client.get(reverse("recipe_detail", args=[self.recipe.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Recipe")

    def test_recipe_edit_view_owner(self):
        response = self.client.get(reverse("edit_recipe", args=[self.recipe.id]))
        self.assertEqual(response.status_code, 200)

    def test_recipe_edit_view_not_owner(self):
        self.client.login(username="otheruser", password="otherpass")
        response = self.client.get(reverse("edit_recipe", args=[self.recipe.id]))
        self.assertRedirects(response, reverse("recipe_detail", args=[self.recipe.id]))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(str(messages[0]), "You cannot edit someone else's recipe.")

    def test_favorite_recipe(self):
        response = self.client.post(reverse("favorite_recipe", args=[self.recipe.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.recipe, self.user.favorite_recipes.all())

    def test_rate_recipe(self):
        response = self.client.post(reverse("recipe_detail", args=[self.recipe.id]), {"rating": 4})
        self.assertEqual(response.status_code, 302)
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.ratings.first().rating, 4)


class IngredientSearchTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.category = Category.objects.create(name="Test Category")
        self.recipe1 = Recipe.objects.create(
            title="Recipe One",
            description="First recipe",
            ingredients=json.dumps(["Flour", "Sugar", "Eggs"]),
            instructions="Mix and bake",
            category=self.category,
            creator=self.user
        )
        self.recipe2 = Recipe.objects.create(
            title="Recipe Two",
            description="Second recipe",
            ingredients=json.dumps(["Butter", "Milk", "Sugar"]),
            instructions="Mix and fry",
            category=self.category,
            creator=self.user
        )
        self.recipe3 = Recipe.objects.create(
            title="Recipe Three",
            description="Third recipe",
            ingredients=json.dumps(["Bread", "Butter"]),
            instructions="Spread butter on bread",
            category=self.category,
            creator=self.user
        )

    def test_find_recipes_by_ingredients_full_match(self):
        results = find_recipes_by_ingredients(["flour", "sugar", "eggs"])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.recipe1)

    def test_find_recipes_by_ingredients_partial_match(self):
        results = find_recipes_by_ingredients(["sugar", "butter"])
        self.assertEqual(len(results), 2)
        self.assertIn(self.recipe1, results)
        self.assertIn(self.recipe2, results)

    def test_shopping_list_generation(self):
        results = find_recipes_by_ingredients(["flour"])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.recipe1)
        # Verify the missing ingredients
        self.assertIn("sugar", self.recipe1.get_ingredients())
        self.assertIn("eggs", self.recipe1.get_ingredients())
    
    def test_ingredient_search_view(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.post(reverse("ingredient_search"), {"ingredients": "butter"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Recipe One")
        self.assertContains(response, "Recipe Two")