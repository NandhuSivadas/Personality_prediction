// Wait for the page to be fully loaded
document.addEventListener("DOMContentLoaded", () => {
    
    // Find the form and the error message container
    const testForm = document.getElementById("test-form");
    const errorMessageDiv = document.getElementById("form-error-message");

    if (testForm) {
        // Add an event listener for when the user tries to submit the form
        testForm.addEventListener("submit", (event) => {
            
            // Get all question blocks on the page
            const questionBlocks = document.querySelectorAll(".question-block");
            let allQuestionsAnswered = true;
            let firstUnanswered = null;

            // Loop through each question block
            questionBlocks.forEach(block => {
                // Check if any radio button *is* checked inside this block
                const isAnswered = block.querySelector("input[type='radio']:checked");

                if (!isAnswered) {
                    allQuestionsAnswered = false;
                    // This is an unanswered question. Add the error class.
                    block.classList.add("question-unanswered");
                    
                    // Keep track of the first unanswered question to scroll to it
                    if (!firstUnanswered) {
                        firstUnanswered = block;
                    }
                } else {
                    // This question *is* answered, so remove the error class
                    // in case it was added on a previous attempt.
                    block.classList.remove("question-unanswered");
                }
            });

            // If any question is unanswered...
            if (!allQuestionsAnswered) {
                // 1. STOP the form from submitting
                event.preventDefault();

                // 2. Display our custom error message
                errorMessageDiv.textContent = "Please answer all 5 questions to continue.";
                errorMessageDiv.style.display = "block"; // Make it visible

                // 3. Scroll to the first unanswered question
                if (firstUnanswered) {
                    firstUnanswered.scrollIntoView({ behavior: "smooth", block: "center" });
                }
            } else {
                // All questions are answered!
                // 1. Hide the error message (if it was showing)
                errorMessageDiv.style.display = "none";
                
                // 2. Allow the form to submit (we don't preventDefault)
            }
        });
    }
});