document.addEventListener('DOMContentLoaded', function() {
    // Initialize all tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize all popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Set current date as default for date inputs
    const dateInputs = document.querySelectorAll('input[type="date"]:not([value])');
    dateInputs.forEach(input => {
        // Only set today's date if there's no value and it's not a readonly field
        if (!input.readOnly && !input.value) {
            const today = new Date().toISOString().split('T')[0];
            input.value = today;
        }
    });
    
    // Confirm deletion actions
    const confirmButtons = document.querySelectorAll('.btn-confirm');
    confirmButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to perform this action?')) {
                e.preventDefault();
            }
        });
    });
    
    // Function to show expiration warning based on date
    function checkExpirationDates() {
        const extracts = document.querySelectorAll('.inventory-extract');
        const today = new Date();
        
        extracts.forEach(extract => {
            const expirationDate = new Date(extract.dataset.expiration);
            const diffTime = expirationDate - today;
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            
            if (diffDays < 0) {
                // Already expired
                extract.classList.add('expired');
                extract.classList.remove('expiring-soon');
            } else if (diffDays <= 30) {
                // Expiring in 30 days or less
                extract.classList.add('expiring-soon');
                extract.classList.remove('expired');
            } else {
                extract.classList.remove('expiring-soon', 'expired');
            }
        });
    }
    
    // Run expiration check if we're on the inventory page
    if (document.querySelector('.inventory-page')) {
        checkExpirationDates();
    }
    
    // Filter functionality for tables
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            const searchValue = this.value.toLowerCase();
            const tableRows = document.querySelectorAll('tbody tr');
            
            tableRows.forEach(row => {
                const text = row.textContent.toLowerCase();
                if (text.includes(searchValue)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
});
