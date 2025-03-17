def generate_recipe(ingredients, dietary_preferences=None):
    """
    Generate a recipe using the provided ingredients and dietary preferences with Groq API.
    
    Args:
        ingredients (list): List of ingredients to use in the recipe
        dietary_preferences (str, optional): Any dietary preferences or restrictions
        
    Returns:
        dict: A dictionary containing the recipe title, ingredients list, and instructions
    """
    try:
        # Initialize Groq client with API key from environment variables
        from groq import Groq
        import os
        
        # Load from environment variables if not already loaded
        if "GROQ_API_KEY" not in os.environ:
            from dotenv import load_dotenv
            load_dotenv()
            
        # Create a new client instance for this function call
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        
        # Join ingredients for the prompt
        ingredients_text = ", ".join(ingredients)
        
        # Build system prompt with detailed instructions for consistent metadata format
        system_prompt = """You are a professional chef creating recipes. Follow these rules strictly:

1. Start with the recipe title in format: **Recipe Title**
2. Do NOT include any introduction like "Here's a recipe" or "What an interesting combination!"
3. Include a clearly labeled **METADATA** section with EXACTLY these fields:
   - Category: [Breakfast/Lunch/Dinner/Dessert/Appetizer/Snack]
   - Allergens: [List all allergens separated by commas, or "None" if none]
   - Prep Time: X minutes
   - Cook Time: X minutes
   - Difficulty: Easy/Medium/Hard
   - Servings: X
4. After the metadata, continue with the actual recipe content

Use exactly this format:

**RECIPE TITLE**

**METADATA**
Category: [Breakfast/Lunch/Dinner/Dessert/Appetizer/Snack]
Allergens: [List all allergens or "None" if none]
Prep Time: X minutes
Cook Time: X minutes
Difficulty: Easy/Medium/Hard
Servings: X

**Ingredients:**
* Ingredient 1 - amount
* Ingredient 2 - amount
(etc.)

**Instructions:**
1. First step
2. Second step
(etc.)"""
        
        # Add dietary preferences to the user prompt
        user_prompt = f"Create a recipe using these ingredients: {ingredients_text}."
        if dietary_preferences:
            user_prompt += f" The recipe should be {dietary_preferences}."
        
        user_prompt += f"\n\nChoose an appropriate meal category for these ingredients. Include all common allergens present in the recipe. The metadata section will be removed from the final display."
        
        # Make the API call to Groq
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
        )
        
        # Extract and format the recipe
        recipe_text = response.choices[0].message.content.strip()
        
        # Ensure the METADATA section is properly formatted (for older responses)
        recipe_text = recipe_text.replace("**METADATA:**", "**METADATA**")
        
        return {
            "success": True,
            "recipe": recipe_text
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }