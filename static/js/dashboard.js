document.addEventListener('DOMContentLoaded', function() {
    // Connect to the WebSocket server
    const socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);
    
    // Initialize charts
    initializeSentimentChart();
    initializeSourceChart();
    
    // Socket event for receiving data updates
    socket.on('update_data', function(data) {
        // Update charts with new data
        updateSentimentChart(data);
        updateSourceChart(data);
        
        // Update the recent items table
        updateRecentItemsTable(data.recent_items);
    });
    
    // Socket event for receiving configuration updates
    socket.on('config_data', function(config) {
        // Update the search terms form with current values
        document.getElementById('search-terms').placeholder = config.search_terms.join(', ');
        document.getElementById('current-terms').textContent = config.search_terms.join(', ');
        document.getElementById('max-items').placeholder = config.max_items;
        
        // Reset the status badge
        updateSearchStatus('Current', 'bg-info');
    });
    
    // Request initial configuration data
    socket.emit('get_config');
    
    // Handle search form submission
    document.getElementById('search-form').addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Get the search terms and max items
        const searchTermsInput = document.getElementById('search-terms').value.trim();
        const maxItemsInput = document.getElementById('max-items').value.trim();
        
        // Validate input
        if (!searchTermsInput && !maxItemsInput) {
            updateSearchStatus('No changes', 'bg-warning');
            return;
        }
        
        // Update status
        updateSearchStatus('Updating...', 'bg-primary');
        
        // Prepare the config data
        const configData = {};
        if (searchTermsInput) {
            configData.search_terms = searchTermsInput;
        }
        if (maxItemsInput) {
            configData.max_items = parseInt(maxItemsInput, 10);
        }
        
        // Send the update to the server
        socket.emit('update_config', configData);
        
        // Clear the form fields
        document.getElementById('search-terms').value = '';
        document.getElementById('max-items').value = '';
    });
    
    // Function to update the search status badge
    function updateSearchStatus(text, className) {
        const statusBadge = document.getElementById('search-status');
        statusBadge.textContent = text;
        
        // Remove all background classes and add the new one
        statusBadge.className = 'badge ' + className;
    }
    
    // Function to initialize the sentiment chart
    function initializeSentimentChart() {
        const data = [{
            values: [0, 0, 0],
            labels: ['Positive', 'Negative', 'Neutral'],
            type: 'pie',
            marker: {
                colors: ['#28a745', '#dc3545', '#6c757d']
            },
            hole: 0.4,
            textinfo: 'label+percent',
            insidetextorientation: 'radial'
        }];
        
        const layout = {
            margin: {
                l: 20,
                r: 20,
                b: 20,
                t: 20
            },
            showlegend: false,
            height: 300
        };
        
        Plotly.newPlot('sentiment-chart', data, layout);
    }
    
    // Function to update the sentiment chart
    function updateSentimentChart(data) {
        const values = [data.positive, data.negative, data.neutral];
        
        Plotly.restyle('sentiment-chart', {
            'values': [values]
        });
    }
    
    // Function to initialize the source chart
    function initializeSourceChart() {
        const data = [{
            values: [0, 0],
            labels: ['Twitter', 'Reddit'],
            type: 'pie',
            marker: {
                colors: ['#1DA1F2', '#FF4500']
            },
            hole: 0.4,
            textinfo: 'label+percent',
            insidetextorientation: 'radial'
        }];
        
        const layout = {
            margin: {
                l: 20,
                r: 20,
                b: 20,
                t: 20
            },
            showlegend: false,
            height: 300
        };
        
        Plotly.newPlot('source-chart', data, layout);
    }
    
    // Function to update the source chart
    function updateSourceChart(data) {
        const values = [data.sources.twitter, data.sources.reddit];
        
        Plotly.restyle('source-chart', {
            'values': [values]
        });
    }
    
    // Function to update the recent items table
    function updateRecentItemsTable(items) {
        const tableBody = document.getElementById('recent-items-table');
        tableBody.innerHTML = '';
        
        // Add the latest 10 items to the table
        items.slice(0, 10).forEach(function(item) {
            const row = document.createElement('tr');
            
            // Source cell
            const sourceCell = document.createElement('td');
            sourceCell.textContent = item.source;
            row.appendChild(sourceCell);
            
            // Text cell (truncated if too long)
            const textCell = document.createElement('td');
            const truncatedText = item.text.length > 100 ? item.text.substring(0, 100) + '...' : item.text;
            textCell.textContent = truncatedText;
            row.appendChild(textCell);
            
            // Sentiment cell with appropriate class
            const sentimentCell = document.createElement('td');
            sentimentCell.textContent = item.sentiment.charAt(0).toUpperCase() + item.sentiment.slice(1);
            sentimentCell.className = item.sentiment;
            row.appendChild(sentimentCell);
            
            // Timestamp cell (formatted)
            const timestampCell = document.createElement('td');
            const timestamp = new Date(item.timestamp);
            timestampCell.textContent = timestamp.toLocaleString();
            row.appendChild(timestampCell);
            
            // Link cell
            const linkCell = document.createElement('td');
            const link = document.createElement('a');
            link.href = item.url;
            link.target = '_blank';
            link.textContent = 'View';
            linkCell.appendChild(link);
            row.appendChild(linkCell);
            
            tableBody.appendChild(row);
        });
    }
});