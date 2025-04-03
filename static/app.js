// Connect to Socket.IO server
const socket = io();

// DOM elements
const sentimentData = document.getElementById('sentiment-data');
const sentimentChart = document.getElementById('sentiment-chart');
const recentItemsList = document.getElementById('recent-items');
const sourceChart = document.getElementById('source-chart');
const configForm = document.getElementById('config-form');
const searchTermsInput = document.getElementById('search-terms');
const maxItemsInput = document.getElementById('max-items');

// System status
let systemMode = 'live'; // 'live', 'demo', or 'error'

// Charts
let sentimentPieChart = null;
let sourcesPieChart = null;

// Socket.io event listeners
socket.on('connect', () => {
    console.log('Connected to server');
    showStatusIndicator('Connecting...', 'active');
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
    showStatusIndicator('Disconnected', 'error');
});

socket.on('update_data', (data) => {
    // Update the visualization with the new data
    updateSentimentData(data);
    updateRecentItems(data.recent_items);
    updateCharts(data);
});

socket.on('config_data', (data) => {
    // Update configuration form with current values
    searchTermsInput.value = data.search_terms.join(',');
    maxItemsInput.value = data.max_items;
});

socket.on('initialization_error', (data) => {
    console.error('Initialization error:', data.error);
    systemMode = 'error';
    showStatusIndicator('Error Mode (Using Sample Data)', 'error');
    showErrorNotification('System Error', data.error);
});

// Initialize the page
document.addEventListener('DOMContentLoaded', () => {
    // Request current configuration
    socket.emit('get_config');
    
    // Set up configuration form
    configForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const searchTerms = searchTermsInput.value;
        const maxItems = parseInt(maxItemsInput.value);
        
        // Validate inputs
        if (!searchTerms.trim()) {
            showErrorNotification('Configuration Error', 'Search terms cannot be empty');
            return;
        }
        
        if (isNaN(maxItems) || maxItems < 1 || maxItems > 1000) {
            showErrorNotification('Configuration Error', 'Max items must be between 1 and 1000');
            return;
        }
        
        // Send updated configuration to server
        socket.emit('update_config', {
            search_terms: searchTerms,
            max_items: maxItems
        });
        
        // Show notification
        showSuccessNotification('Configuration Updated', 'Your changes have been applied');
    });
    
    // Initialize charts
    initializeCharts();
});

// Function to update sentiment data display
function updateSentimentData(data) {
    const total = data.positive + data.negative + data.neutral;
    
    if (total === 0) {
        sentimentData.innerHTML = '<p>No sentiment data available yet. Please wait...</p>';
        return;
    }
    
    // If we have Twitter or Reddit data, update system mode
    if (data.sources.twitter > 0 || data.sources.reddit > 0) {
        if (systemMode !== 'error') {
            systemMode = data.sources.twitter > 0 || data.sources.reddit > 0 ? 'live' : 'demo';
            const statusText = systemMode === 'live' ? 'Live Mode' : 'Demo Mode (Sample Data)';
            showStatusIndicator(statusText, systemMode);
        }
    }
    
    // Format percentages
    const positivePercent = (data.positive / total * 100).toFixed(1);
    const negativePercent = (data.negative / total * 100).toFixed(1);
    const neutralPercent = (data.neutral / total * 100).toFixed(1);
    
    sentimentData.innerHTML = `
        <div class="sentiment-summary">
            <div class="sentiment-card positive">
                <h3>Positive</h3>
                <div class="sentiment-value">${data.positive}</div>
                <div class="sentiment-percent">${positivePercent}%</div>
            </div>
            <div class="sentiment-card negative">
                <h3>Negative</h3>
                <div class="sentiment-value">${data.negative}</div>
                <div class="sentiment-percent">${negativePercent}%</div>
            </div>
            <div class="sentiment-card neutral">
                <h3>Neutral</h3>
                <div class="sentiment-value">${data.neutral}</div>
                <div class="sentiment-percent">${neutralPercent}%</div>
            </div>
        </div>
    `;
}

// Function to update the list of recent items
function updateRecentItems(items) {
    if (!items || items.length === 0) {
        recentItemsList.innerHTML = '<p class="no-data">No recent items available.</p>';
        return;
    }
    
    recentItemsList.innerHTML = '';
    
    items.forEach(item => {
        const timestamp = new Date(item.timestamp);
        const timeAgo = getTimeAgo(timestamp);
        
        const itemElement = document.createElement('div');
        itemElement.className = `recent-item ${item.sentiment}`;
        
        itemElement.innerHTML = `
            <div class="item-header">
                <span class="item-source">${item.source}</span>
                <span class="item-time">${timeAgo}</span>
            </div>
            <div class="item-content">${item.text}</div>
            ${item.url ? `<a href="${item.url}" target="_blank" class="item-link">View Original</a>` : ''}
        `;
        
        recentItemsList.appendChild(itemElement);
    });
}

// Function to initialize charts
function initializeCharts() {
    // Sentiment distribution chart
    const sentimentCtx = sentimentChart.getContext('2d');
    sentimentPieChart = new Chart(sentimentCtx, {
        type: 'pie',
        data: {
            labels: ['Positive', 'Negative', 'Neutral'],
            datasets: [{
                data: [0, 0, 0],
                backgroundColor: ['#4CAF50', '#F44336', '#2196F3']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right'
                },
                title: {
                    display: true,
                    text: 'Sentiment Distribution'
                }
            }
        }
    });
    
    // Source distribution chart
    const sourceCtx = sourceChart.getContext('2d');
    sourcesPieChart = new Chart(sourceCtx, {
        type: 'pie',
        data: {
            labels: ['Twitter', 'Reddit'],
            datasets: [{
                data: [0, 0],
                backgroundColor: ['#1DA1F2', '#FF5700']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right'
                },
                title: {
                    display: true,
                    text: 'Data Sources'
                }
            }
        }
    });
}

// Function to update charts with new data
function updateCharts(data) {
    // Update sentiment chart
    sentimentPieChart.data.datasets[0].data = [
        data.positive,
        data.negative,
        data.neutral
    ];
    sentimentPieChart.update();
    
    // Update source chart
    sourcesPieChart.data.datasets[0].data = [
        data.sources.twitter,
        data.sources.reddit
    ];
    sourcesPieChart.update();
}

// Helper function to calculate time ago
function getTimeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);
    
    let interval = Math.floor(seconds / 31536000);
    if (interval > 1) return interval + ' years ago';
    if (interval === 1) return '1 year ago';
    
    interval = Math.floor(seconds / 2592000);
    if (interval > 1) return interval + ' months ago';
    if (interval === 1) return '1 month ago';
    
    interval = Math.floor(seconds / 86400);
    if (interval > 1) return interval + ' days ago';
    if (interval === 1) return '1 day ago';
    
    interval = Math.floor(seconds / 3600);
    if (interval > 1) return interval + ' hours ago';
    if (interval === 1) return '1 hour ago';
    
    interval = Math.floor(seconds / 60);
    if (interval > 1) return interval + ' minutes ago';
    if (interval === 1) return '1 minute ago';
    
    return Math.floor(seconds) + ' seconds ago';
}

// Function to show a system status indicator
function showStatusIndicator(text, status) {
    // Remove existing status indicator if present
    const existingStatus = document.querySelector('.system-status');
    if (existingStatus) {
        existingStatus.remove();
    }
    
    // Create new status indicator
    const statusEl = document.createElement('div');
    statusEl.className = 'system-status';
    
    statusEl.innerHTML = `
        <div class="status-indicator ${status}"></div>
        <span>${text}</span>
    `;
    
    document.body.appendChild(statusEl);
}

// Function to show error notification
function showErrorNotification(title, message) {
    showNotification(title, message, 'error');
}

// Function to show success notification
function showSuccessNotification(title, message) {
    showNotification(title, message, 'success');
}

// General notification function
function showNotification(title, message, type = 'error') {
    // Remove existing notification if present
    const existingNotification = document.querySelector('.error-notification, .success-notification');
    if (existingNotification) {
        existingNotification.remove();
    }
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = type === 'error' ? 'error-notification' : 'success-notification';
    
    // Add content
    notification.innerHTML = `
        <i class="${type === 'error' ? 'fas fa-exclamation-circle' : 'fas fa-check-circle'}"></i>
        <div>
            <strong>${title}</strong>
            <p>${message}</p>
        </div>
        <button class="close-btn">&times;</button>
    `;
    
    // Add to document
    document.body.appendChild(notification);
    
    // Add close button functionality
    const closeBtn = notification.querySelector('.close-btn');
    closeBtn.addEventListener('click', () => {
        notification.classList.add('hidden');
        setTimeout(() => notification.remove(), 300);
    });
    
    // Auto hide after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.classList.add('hidden');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 300);
        }
    }, 5000);
} 