// AgriConnect Core JavaScript Utilities
document.addEventListener("DOMContentLoaded", function () {
    // Automatically dismiss flash alerts after 5 seconds if desired
    const alerts = document.querySelectorAll(".alert-dismissible");
    alerts.forEach((alert) => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 5000);
    });
});
