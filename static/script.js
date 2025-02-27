// Add animation to success messages
document.addEventListener('DOMContentLoaded', function() {
    // Animate flash messages
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-20px)';
        
        setTimeout(() => {
            alert.style.transition = 'all 0.5s ease-in-out';
            alert.style.opacity = '1';
            alert.style.transform = 'translateY(0)';
        }, 100);
    });

    // Auto-dismiss alerts after 5 seconds
    setTimeout(() => {
        alerts.forEach(alert => {
            const closeButton = alert.querySelector('.btn-close');
            if (closeButton) {
                closeButton.click();
            }
        });
    }, 5000);
});
