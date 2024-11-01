# 🍽️ Recipe Sharing Platform

Welcome to the **Recipe Sharing Platform**, a web application designed for food lovers to discover, create, and share their favorite recipes. Registered users can manage their personal recipe collections, rate dishes, and favorite recipes they love the most. This platform combines Django's robust backend capabilities with a responsive, modern Bootstrap interface.

## 🌟 Features

### 1. User Authentication
- **Sign Up / Log In**: Users can register, log in, and log out securely.
- **Profile Management**: Update profile details like username and email.
  
### 2. Recipe Management
- **Create Recipes**: Users can add new recipes by filling in details like title, description, ingredients, instructions, and selecting a category.
- **Edit & Delete**: Users can edit and delete their own recipes at any time.

### 3. Recipe Interaction
- **Favorite Recipes**: Users can favorite or unfavorite recipes.
- **Recipe Ratings**: Users can rate recipes on a scale of 1 to 5, and see the average rating.
  
### 4. Recipe Categories
- **Categorization**: Recipes are grouped into categories like Breakfast, Lunch, and Dinner, making it easy to explore based on type.

### 5. User-Friendly Design
- **Responsive Design**: The app is fully responsive, ensuring it works seamlessly across desktops, tablets, and smartphones.
- **Clean UI**: The platform is built using Bootstrap for a sleek, modern look.

## 🛠️ Technologies Used

- **Django**: Backend framework that handles user authentication, data storage, and overall application logic.
- **Bootstrap**: Frontend framework for responsive and mobile-first web development.
- **HTML/CSS**: For rendering and styling the UI.
- **JavaScript**: Enhances user interaction on the frontend.
- **PostgreSQL**: Database to store user data, recipes, and ratings.

## ⚙️ Installation

To run the Recipe Sharing Platform locally, follow these steps:

### Prerequisites

- Python 3.x
- Django 3.x
- Virtual environment support

### Steps

1. **Clone the repository**:

   ```bash
   git clone https://github.com/m75-ali/recipe-sharing-platform.git

2. **Navigate to the project directory**:

   ```bash
   cd recipe-sharing-platform

3. **Create and activate a virtual environment**:

   ```bash
   python -m venv env
   source env/bin/activate  # On Windows, use `env\Scripts\activate`

4. **Install the dependencies**:

   ```bash
   pip install -r requirements.txt

5. **Apply the migrations**:

   ```bash
   python manage.py migrate
   
6. **Create a superuser** for the Django admin panel:

   ```bash
   python manage.py createsuperuser

7. **Run the development server**:

   ```bash
   python manage.py runserver

8. **Visit this URL in browser**:
   http://127.0.0.1:8000 in your browser to view the app.
