/**
 * 5K Tracker PWA Registration and Utilities
 * Handles service worker registration and PWA features
 */

(function() {
    'use strict';

    // Service Worker Registration
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', function() {
            navigator.serviceWorker.register('/tracker/static/service-worker.js', {
                scope: '/tracker/'
            })
            .then(function(registration) {
                console.log('Service Worker registered successfully:', registration.scope);
                
                // Check for updates
                registration.addEventListener('updatefound', function() {
                    const newWorker = registration.installing;
                    newWorker.addEventListener('statechange', function() {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            // New version available
                            showUpdateAvailableNotification();
                        }
                    });
                });
            })
            .catch(function(error) {
                console.log('Service Worker registration failed:', error);
            });
        });
    }

    // PWA Install Prompt
    let deferredPrompt;
    const installButton = document.createElement('button');
    installButton.textContent = 'Install App';
    installButton.className = 'btn btn-outline-primary btn-sm position-fixed';
    installButton.style.cssText = 'bottom: 20px; right: 20px; z-index: 1050; display: none;';
    installButton.id = 'install-button';

    window.addEventListener('beforeinstallprompt', function(e) {
        // Prevent the mini-infobar from appearing on mobile
        e.preventDefault();
        deferredPrompt = e;
        
        // Show the install button
        document.body.appendChild(installButton);
        installButton.style.display = 'block';
        
        installButton.addEventListener('click', function() {
            // Hide the install button
            installButton.style.display = 'none';
            
            // Show the install prompt
            deferredPrompt.prompt();
            
            deferredPrompt.userChoice.then(function(choiceResult) {
                if (choiceResult.outcome === 'accepted') {
                    console.log('User accepted the install prompt');
                } else {
                    console.log('User dismissed the install prompt');
                }
                deferredPrompt = null;
            });
        });
    });

    // Handle app installed
    window.addEventListener('appinstalled', function(e) {
        console.log('5K Tracker PWA was installed');
        // Hide install button if still visible
        if (installButton.parentNode) {
            installButton.style.display = 'none';
        }
        
        // Show success message
        showToast('App installed successfully! You can now access 5K Tracker from your home screen.', 'success');
    });

    // Check if app is running in standalone mode
    function isRunningStandalone() {
        return window.matchMedia('(display-mode: standalone)').matches ||
               window.navigator.standalone === true;
    }

    // Add PWA-specific styling when running standalone
    if (isRunningStandalone()) {
        document.addEventListener('DOMContentLoaded', function() {
            document.body.classList.add('pwa-standalone');
            
            // Add some standalone-specific styles
            const style = document.createElement('style');
            style.textContent = `
                .pwa-standalone .navbar {
                    padding-top: env(safe-area-inset-top, 0);
                }
                .pwa-standalone .container {
                    padding-left: max(15px, env(safe-area-inset-left));
                    padding-right: max(15px, env(safe-area-inset-right));
                }
            `;
            document.head.appendChild(style);
        });
    }

    // Network status monitoring
    function updateOnlineStatus() {
        const statusElement = document.getElementById('network-status');
        if (statusElement) {
            if (navigator.onLine) {
                statusElement.textContent = '';
                statusElement.classList.remove('offline');
            } else {
                statusElement.textContent = 'You are currently offline. Some features may be limited.';
                statusElement.classList.add('offline');
            }
        }
    }

    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);

    // Add network status indicator to the page
    document.addEventListener('DOMContentLoaded', function() {
        const networkStatus = document.createElement('div');
        networkStatus.id = 'network-status';
        networkStatus.className = 'alert alert-warning text-center';
        networkStatus.style.cssText = 'margin: 0; border-radius: 0; display: none;';
        
        const navbar = document.querySelector('.navbar');
        if (navbar && navbar.nextSibling) {
            navbar.parentNode.insertBefore(networkStatus, navbar.nextSibling);
        }
        
        // Initial status check
        updateOnlineStatus();
        
        // Show/hide based on content
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList' || mutation.type === 'characterData') {
                    const hasContent = networkStatus.textContent.trim().length > 0;
                    networkStatus.style.display = hasContent ? 'block' : 'none';
                }
            });
        });
        
        observer.observe(networkStatus, { childList: true, characterData: true, subtree: true });
    });

    // Utility function to show toast messages
    function showToast(message, type = 'info') {
        const toastContainer = getOrCreateToastContainer();
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        // Initialize and show the toast
        if (typeof bootstrap !== 'undefined') {
            const bsToast = new bootstrap.Toast(toast, { delay: 5000 });
            bsToast.show();
            
            toast.addEventListener('hidden.bs.toast', function() {
                toast.remove();
            });
        } else {
            // Fallback if Bootstrap JS is not loaded
            setTimeout(function() {
                toast.remove();
            }, 5000);
        }
    }

    function getOrCreateToastContainer() {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            container.style.zIndex = '1055';
            document.body.appendChild(container);
        }
        return container;
    }

    function showUpdateAvailableNotification() {
        showToast(
            'A new version of the app is available. <button class="btn btn-sm btn-light ms-2" onclick="window.location.reload()">Update Now</button>',
            'primary'
        );
    }

    // Background sync for offline form submissions (if supported)
    if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
        // Register for background sync when forms are submitted offline
        document.addEventListener('submit', function(e) {
            if (!navigator.onLine && e.target.method === 'post') {
                e.preventDefault();
                
                // Store form data for later sync
                const formData = new FormData(e.target);
                const data = Object.fromEntries(formData.entries());
                
                // Store in localStorage for sync when online
                const pendingData = JSON.parse(localStorage.getItem('pendingRaceData') || '[]');
                pendingData.push({
                    url: e.target.action,
                    data: data,
                    timestamp: Date.now()
                });
                localStorage.setItem('pendingRaceData', JSON.stringify(pendingData));
                
                showToast('Form saved offline. It will be submitted when you\'re back online.', 'warning');
                
                // Register for background sync
                navigator.serviceWorker.ready.then(function(registration) {
                    return registration.sync.register('race-sync');
                });
            }
        });
    }

    // Expose utility functions globally
    window.PWAUtils = {
        showToast: showToast,
        isRunningStandalone: isRunningStandalone,
        updateOnlineStatus: updateOnlineStatus
    };

})();