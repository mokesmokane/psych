document.addEventListener('DOMContentLoaded', function() {
    console.log('DOMContentLoaded');
    // Initialize Socket.IO
    const socket = io();
    
    socket.on('connect', () => {
        console.log('Socket.IO client connected');
    });
 
    socket.on('connect_error', (err) => {
        console.error('Connection failed:', err);
    });

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
            const iterations = parseInt(formData.get('iterations'), 10);
            
            // Show processing status
            processingStatus.style.display = 'block';
            processingStatus.textContent = 'Processing images...';
            
            fetch('/process_image', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Processing started successfully, status is already shown
                } else {
                    processingStatus.style.display = 'none';
                    alert('Error: ' + data.error);
                }
            })
            .catch(error => {
                processingStatus.style.display = 'none';
                console.error('Error:', error);
                alert('An error occurred while processing the image.');
            });
        });
    }

    // Listen for 'joined' event to confirm connection
    socket.on('joined', function(data) {
        console.log('Joined room:', data.room);
    });

    // Listen for processed images
    // socket.on('image_processed', function(data) {
    //     console.log('Received processed image:', data);
    //     const img = document.createElement('img');
    //     img.src = 'data:image/png;base64,' + data.image_data;
    //     img.classList.add('processed-image');

    //     const container = document.getElementById('processed-images-container');
    //     if (container) {
    //         // based on the iteration number, add the image to the correct position
    //         container.children[data.iteration - 1].src = img.src;
    //     } else {
    //         console.error('Container not found');
    //     }

    //     // // Update processing status
    //     // if (processingStatus) {
    //     //     const iterations = parseInt(document.getElementById('iterations').value, 10);
    //     //     processingStatus.textContent = `Processing... ${data.iteration} of ${iterations} complete`;
    //     //     if (data.iteration === iterations) {
    //     //         processingStatus.textContent = 'Processing complete!';
    //     //         setTimeout(() => {
    //     //             processingStatus.style.display = 'none';
    //     //         }, 3000);
    //     //     }
    //     // }
    // });
    // // Listen for final image and display it instead of the initial image
    // socket.on('final_image_processed', function(data) {
    //     console.log('Received final processed image:', data);
    //     const img = document.createElement('img');
    //     img.src = 'data:image/png;base64,' + data.image_data;
    //     img.classList.add('processed-image');

    //     const container = document.getElementById('image-preview');
    //     container.src = img.src;

    // });

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
