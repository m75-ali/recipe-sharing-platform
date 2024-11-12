document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('filter-form');
    const recipesContainer = document.getElementById('recipes-container');

    form.addEventListener('submit', function (event) {
        event.preventDefault(); // Prevent full page reload

        const formData = new FormData(form);
        const category = formData.get('category');
        const url = category ? `/recipes/?category=${category}` : '/recipes/';

        // Perform the AJAX request
        fetch(url, {
            headers: {
                'x-requested-with': 'XMLHttpRequest', // Mark this as an AJAX request
            },
        })
            .then(response => response.json())
            .then(data => {
                // Update the recipe list with the returned HTML
                recipesContainer.innerHTML = data.html;
            })
            .catch(error => console.error('Error fetching recipes:', error));
    });
});