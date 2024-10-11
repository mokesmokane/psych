document.addEventListener('DOMContentLoaded', function() {
    // Image upload preview
    const imageUpload = document.getElementById('image-upload');
    const imagePreview = document.getElementById('image-preview');

    if (imageUpload && imagePreview) {
        imageUpload.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    imagePreview.src = e.target.result;
                    imagePreview.style.display = 'block';
                }
                reader.readAsDataURL(file);
            }
        });
    }

    // Process image form submission
    const processForm = document.getElementById('process-form');
    const processingStatus = document.getElementById('processing-status');
    if (processForm) {
        processForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            
            // Show processing status
            processingStatus.style.display = 'block';
            
            fetch('/process_image', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                // Hide processing status
                processingStatus.style.display = 'none';
                
                if (data.success) {
                    alert('Image processed successfully!');
                    window.location.href = '/dashboard';
                } else {
                    alert('Error: ' + data.error);
                }
            })
            .catch(error => {
                // Hide processing status
                processingStatus.style.display = 'none';
                
                console.error('Error:', error);
                alert('An error occurred while processing the image.');
            });
        });
    }

    // Stripe payment button
    const stripeButton = document.getElementById('stripe-button');
    if (stripeButton) {
        stripeButton.addEventListener('click', function(e) {
            e.preventDefault();
            fetch('/create-checkout-session', {
                method: 'POST',
            })
            .then(function(response) {
                return response.json();
            })
            .then(function(session) {
                return stripe.redirectToCheckout({ sessionId: session.id });
            })
            .then(function(result) {
                if (result.error) {
                    alert(result.error.message);
                }
            })
            .catch(function(error) {
                console.error('Error:', error);
            });
        });
    }
});
