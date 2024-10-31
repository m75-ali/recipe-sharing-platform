from django.test import TestCase
from django.contrib.auth.models import User
from .models import Recipe, Category
from django.urls import reverse

class RecipeModelTest(TestCase):
    
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username="testuser", password="testpass")
        # Create a category
        self.category = Category.objects.create(name="Test Category")

    def test_recipe_str_method(self):
        # Create a test recipe
        recipe = Recipe.objects.create(
            title="Test Recipe",
            description="Test description",
            ingredients="Test ingredients",
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
            ingredients="Ingredients for new recipe",
            instructions="Instructions for new recipe",
            category=self.category,
            creator=self.user
        )
        self.assertEqual(Recipe.objects.count(), recipe_count + 1)


class RecipeViewTest(TestCase):
    
    def setUp(self):
        # Set up test user and category
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.other_user = User.objects.create_user(username="otheruser", password="otherpass")
        self.category = Category.objects.create(name="Test Category")
        self.recipe = Recipe.objects.create(
            title="Test Recipe",
            description="Test description",
            ingredients="Test ingredients",
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
        # Only allow the owner to edit
        response = self.client.get(reverse("edit_recipe", args=[self.recipe.id]))
        self.assertEqual(response.status_code, 200)

    def test_recipe_edit_view_not_owner(self):
        # Log in as another user
        self.client.login(username="otheruser", password="otherpass")
        response = self.client.get(reverse("edit_recipe", args=[self.recipe.id]))
        self.assertRedirects(response, reverse("recipe_detail", args=[self.recipe.id]))
        messages = list(response.wsgi_request._messages)
        self.assertEqual(str(messages[0]), "You cannot edit someone else's recipe.")  # Updated message

    def test_favorite_recipe(self):
        # Favorite a recipe
        response = self.client.post(reverse("favorite_recipe", args=[self.recipe.id]))
        self.assertEqual(response.status_code, 302)  # Should redirect after action
        self.assertIn(self.recipe, self.user.favorite_recipes.all())

    def test_rate_recipe(self):
        response = self.client.post(reverse("recipe_detail", args=[self.recipe.id]), {"rating": 4})
        self.assertEqual(response.status_code, 302)  # Should redirect after rating
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.ratings.first().rating, 4)