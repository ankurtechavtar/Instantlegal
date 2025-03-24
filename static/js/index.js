 // Set the target date for the countdown (24 hours from now)
 const targetDate = new Date().getTime() + 24 * 60 * 60 * 1000;

 // Update the countdown every 1 second
 const countdownInterval = setInterval(function() {
     // Get the current time
     const currentTime = new Date().getTime();

     // Calculate the remaining time
     const remainingTime = targetDate - currentTime;

     // Calculate hours, minutes, and seconds
     const hours = Math.floor((remainingTime % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
     const minutes = Math.floor((remainingTime % (1000 * 60 * 60)) / (1000 * 60));
     const seconds = Math.floor((remainingTime % (1000 * 60)) / 1000);

     // Display the results in the respective elements
     document.getElementById("hours").innerHTML = hours.toString().padStart(2, "0");
     document.getElementById("minutes").innerHTML = minutes.toString().padStart(2, "0");
     document.getElementById("seconds").innerHTML = seconds.toString().padStart(2, "0");

     // If the countdown ends, display a message
     if (remainingTime < 0) {
         clearInterval(countdownInterval);
         document.querySelector(".special-offer-timer").innerHTML = "<h2>Offer Expired</h2>";
     }
 }, 1000); // 1000ms = 1 second
// Initialize Stripe
const stripe = Stripe('{{ stripe_key }}');

// Handle form submission

// Capture the Preview button click event
// Ensure that the DOM is fully loaded before attaching event listeners
// Ensure that the DOM is fully loaded before attaching event listeners
// Ensure that the DOM is fully loaded before attaching event listeners
document.addEventListener('DOMContentLoaded', function () {
    // Preview button click handler
    document.getElementById('preview-btn').addEventListener('click', function () {
        const formData = new FormData(document.getElementById('document-form'));

        // Send a request to the preview route
        fetch('/preview-document', {
            method: 'POST',
            body: formData
        }).then(response => response.json())
        .then(data => {
            if (data.error) {
                alert('Error: ' + data.error);
            } else {
                // Display the preview in the modal
                document.getElementById('preview-text').innerHTML = data.document_text;
                document.getElementById('preview-modal').style.display = 'block';

                // Make the fields editable (Assuming you use contenteditable for dynamic fields)
                const editableFields = document.querySelectorAll('#preview-text [contenteditable="true"]');
                editableFields.forEach(field => {
                    field.setAttribute('contenteditable', 'true');
                });
            }
        }).catch(err => {
            alert('Error: ' + err.message);
        });
    });

    // Update Button to capture changes in preview and update the form fields
    document.getElementById('update-btn').addEventListener('click', function () {
        // Collect all dynamically generated editable fields inside the preview modal
        const editableFields = document.querySelectorAll('#preview-text [contenteditable="true"]');

        // Iterate over the editable fields and update the corresponding form fields
        editableFields.forEach(field => {
            const fieldName = field.getAttribute('data-name');  // Assuming you store a data-name attribute for each field
            const fieldValue = field.innerText.trim();  // Capture the updated value

            if (fieldName && fieldValue !== "") {
                // Update the corresponding form field based on data-name attribute
                const formField = document.getElementById(fieldName);
                if (formField) {
                    formField.value = fieldValue;  // Update form field with modified value
                }
            }
        });

        // Hide the preview modal after updating form fields
        document.getElementById('preview-modal').style.display = 'none';
    });

    // Capture form submission for generating the document (when user clicks 'Generate Document Now')
    document.getElementById('document-form').addEventListener('submit', function (event) {
        event.preventDefault();

        // Ensure updates are applied before form submission
        document.getElementById('update-btn').click();

        // Show loading state
        const submitButton = document.querySelector('.submit-btn');
        const originalButtonText = submitButton.innerHTML;
        submitButton.innerHTML = 'Processing...';
        submitButton.disabled = true;

        // Get form data and send it to the server for document generation
        const formData = new FormData(this);

        fetch('/generate-document', {
            method: 'POST',
            body: formData
        }).then(response => response.json())
        .then(data => {
            if (data.error) {
                alert('Error: ' + data.error);
            } else {
                window.location.href = data.download_url;
            }
        }).catch(err => {
            alert('Error: ' + err.message);
        }).finally(() => {
            submitButton.innerHTML = originalButtonText;
            submitButton.disabled = false;
        });
    });
});

    
// Tab functionality for document previews
document.addEventListener('DOMContentLoaded', function() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Remove active class from all buttons and contents
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Add active class to clicked button and corresponding content
            button.classList.add('active');
            const tabId = button.getAttribute('data-tab');
            document.getElementById(`${tabId}-content`).classList.add('active');
        });
    });
    
    // FAQ toggle functionality
    const faqQuestions = document.querySelectorAll('.faq-question');
    
    faqQuestions.forEach(question => {
        question.addEventListener('click', () => {
            const faqItem = question.parentElement;
            faqItem.classList.toggle('active');
            
            // Update the toggle symbol
            const toggle = question.querySelector('.faq-toggle');
            if (faqItem.classList.contains('active')) {
                toggle.textContent = '−';
            } else {
                toggle.textContent = '+';
            }
        });
    });
});