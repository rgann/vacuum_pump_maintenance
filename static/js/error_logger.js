// Error logger for debugging JavaScript issues
console.log('Error logger initialized');

// Log any unhandled errors
window.addEventListener('error', function(event) {
    console.error('Unhandled error:', event.error);
    
    // Create a visible error message for debugging
    const errorDiv = document.createElement('div');
    errorDiv.style.position = 'fixed';
    errorDiv.style.bottom = '10px';
    errorDiv.style.right = '10px';
    errorDiv.style.backgroundColor = 'rgba(255, 0, 0, 0.8)';
    errorDiv.style.color = 'white';
    errorDiv.style.padding = '10px';
    errorDiv.style.borderRadius = '5px';
    errorDiv.style.zIndex = '9999';
    errorDiv.style.maxWidth = '80%';
    errorDiv.style.wordBreak = 'break-word';
    
    errorDiv.textContent = `JavaScript Error: ${event.error.message}`;
    
    document.body.appendChild(errorDiv);
    
    // Remove after 10 seconds
    setTimeout(() => {
        if (document.body.contains(errorDiv)) {
            document.body.removeChild(errorDiv);
        }
    }, 10000);
});
