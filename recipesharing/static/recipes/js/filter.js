// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    const filterForm = document.getElementById('filter-form');
    const categorySelect = document.getElementById('category-select');
    const allergenSelect = document.getElementById('allergen-select');
    const recipesContainer = document.getElementById('recipes-container');

    // Function to update recipes via AJAX
    function updateRecipes() {
        // Create form data from the form
        const formData = new FormData(filterForm);
        
        // Convert form data to URL parameters
        const params = new URLSearchParams(formData);
        
        // Make AJAX request
        fetch(`${window.location.pathname}?${params.toString()}`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            recipesContainer.innerHTML = data.html;
            
            // Update URL with new parameters without reloading the page
            const url = new URL(window.location);
            
            // Clear existing parameters
            url.search = '';
            
            // Add new parameters
            for (const [key, value] of params.entries()) {
                url.searchParams.append(key, value);
            }
            
            window.history.pushState({}, '', url);
        })
        .catch(error => console.error('Error:', error));
    }

    // Add event listeners to both select elements
    if (categorySelect) {
        categorySelect.addEventListener('change', function() {
            updateRecipes();
        });
    }
    
    if (allergenSelect) {
        allergenSelect.addEventListener('change', function() {
            updateRecipes();
        });
    }
});