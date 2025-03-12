from groq import Groq
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Initialize Groq client with API key
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

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
        # Build the prompt based on ingredients and dietary preferences
        prompt = f"Generate a recipe using these ingredients: {', '.join(ingredients)}."
        if dietary_preferences:
            prompt += f" The recipe should be suitable for {dietary_preferences} diet."
        
        # Make the API call to Groq
        response = client.chat.completions.create(
            model="llama3-70b-8192",  # You can also use "mixtral-8x7b-32768" or other available models
            messages=[
                {"role": "system", "content": "You are a professional chef. Generate detailed recipes with clear instructions, ingredients with measurements, cooking time, and difficulty level."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        
        # Extract and format the recipe
        recipe_text = response.choices[0].message.content.strip()
        
        return {
            "success": True,
            "recipe": recipe_text
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# For testing purposes
if __name__ == "__main__":
    test_ingredients = ["chicken", "rice", "bell peppers"]
    result = generate_recipe(test_ingredients)
    print(result)