// This function runs when the page is loaded
document.addEventListener("DOMContentLoaded", () => {
    
    const particleCount = 250; 
    const body = document.body;

    const colors = [
        'var(--color-primary)',   // Your main purple
        '#20c997',              // The green button color
        '#ff9f43',              // The orange button color
        '#e73c7e',              // A bright pink
        '#23a6d5',              // A bright blue
        '#a29bfe'               // The light purple gradient color
    ];

    // --- PART 1: Create all the particles ---
    for (let i = 0; i < particleCount; i++) {
        
        // --- THIS IS THE NEW STRUCTURE ---
        // 1. Create the outer wrapper (for mouse movement)
        const outerWrapper = document.createElement("span");
        outerWrapper.className = "body-bg-shape";
        
        // 2. Create the inner shape (for the float animation)
        const innerShape = document.createElement("span");
        innerShape.className = "body-bg-shape-inner";
        // --- END NEW STRUCTURE ---
        
        // Random size (from 10px to 35px)
        const size = Math.floor(Math.random() * 25) + 10;
        // Apply size to the OUTER wrapper
        outerWrapper.style.width = `${size}px`;
        outerWrapper.style.height = `${size}px`;

        // Random position
        outerWrapper.style.top = `${Math.random() * 100}%`;
        outerWrapper.style.left = `${Math.random() * 100}%`;

        // Random strength for the mouse effect
        const strength = Math.random() * 0.25 + 0.05;
        outerWrapper.dataset.strength = strength; 

        // Random animation delay
        const delay = Math.random() * -60;
        // Apply delay and color to the INNER shape
        innerShape.style.animationDelay = `${delay}s`;
        innerShape.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];

        // --- Build the final element ---
        outerWrapper.appendChild(innerShape); // Put the shape inside the wrapper
        body.appendChild(outerWrapper);     // Add the wrapper to the page
    }

    // --- PART 2: The Mouse-Move Handler ---
    
    // This part stays almost the same!
    const shapes = document.querySelectorAll(".body-bg-shape"); // We still grab the outer wrapper
    const xCenter = window.innerWidth / 2;
    const yCenter = window.innerHeight / 2;

    document.addEventListener("mousemove", (e) => {
        const mouseX = e.clientX;
        const mouseY = e.clientY;

        shapes.forEach((shape) => {
            const strength = parseFloat(shape.dataset.strength) || 0.1;
            const moveX = (mouseX - xCenter) * strength;
            const moveY = (mouseY - yCenter) * strength;
            shape.style.transform = `translate3d(${moveX}px, ${moveY}px, 0)`;
        });
    });
});