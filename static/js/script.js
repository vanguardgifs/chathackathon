document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const refreshLogsButton = document.getElementById('refresh-logs-button');
    
    // Auto-resize textarea as user types
    userInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
    
    // Send message when user presses Enter (without Shift)
    userInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Send message when user clicks send button
    sendButton.addEventListener('click', sendMessage);
    
    // Refresh logs when user clicks refresh button
    refreshLogsButton.addEventListener('click', refreshLogs);
    
    function refreshLogs() {
        // Prevent multiple clicks
        if (refreshLogsButton.classList.contains('loading')) {
            return;
        }
        
        // Show loading state
        refreshLogsButton.classList.add('loading');
        const originalText = refreshLogsButton.innerHTML;
        refreshLogsButton.innerHTML = '<i class="fas fa-sync-alt"></i> Refreshing...';
        
        // Call the refresh logs endpoint
        fetch('/api/refresh-logs', {
            method: 'POST',
        })
        .then(response => response.json())
        .then(data => {
            // Add system message to chat
            if (data.status === 'success') {
                addMessage('Lambda logs have been refreshed. You can now ask questions about the latest logs.', 'bot');
            } else {
                addMessage(`Failed to refresh logs: ${data.message}`, 'bot');
            }
        })
        .catch(error => {
            console.error('Error refreshing logs:', error);
            addMessage('Sorry, I encountered an error while refreshing the logs. Please try again.', 'bot');
        })
        .finally(() => {
            // Reset button state
            refreshLogsButton.classList.remove('loading');
            refreshLogsButton.innerHTML = originalText;
        });
    }
    
    function sendMessage() {
        const message = userInput.value.trim();
        
        if (message === '') return;
        
        // Add user message to chat
        addMessage(message, 'user');
        
        // Clear input and reset height
        userInput.value = '';
        userInput.style.height = 'auto';
        
        // Disable input while waiting for response
        userInput.disabled = true;
        sendButton.disabled = true;
        
        // Show typing indicator
        showTypingIndicator();
        
        // Create a message div for the bot response
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', 'bot');
        
        const messageContent = document.createElement('div');
        messageContent.classList.add('message-content');
        messageContent.innerHTML = ''; // Start empty
        
        messageDiv.appendChild(messageContent);
        
        // Add the empty message div to the chat
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Connect to the server-sent events endpoint
        const eventSource = new EventSource(`/api/chat?message=${encodeURIComponent(message)}`);
        
        // Handle streaming response
        eventSource.onmessage = function(event) {
            // Remove typing indicator if it exists
            removeTypingIndicator();
            
            const data = JSON.parse(event.data);
            
            if (data.error) {
                // Handle error
                messageContent.innerHTML = 'Sorry, I encountered an error. Please try again.';
                eventSource.close();
                
                // Re-enable input
                userInput.disabled = false;
                sendButton.disabled = false;
                userInput.focus();
                return;
            }
            
            if (data.done) {
                // Response is complete
                eventSource.close();
                
                // Re-enable input
                userInput.disabled = false;
                sendButton.disabled = false;
                userInput.focus();
                return;
            }
            
            if (data.chunk) {
                // Append the chunk to the message
                const processedChunk = processText(data.chunk);
                messageContent.innerHTML += processedChunk + ' ';
                
                // Scroll to bottom
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        };
        
        // Handle errors
        eventSource.onerror = function(error) {
            console.error('EventSource error:', error);
            eventSource.close();
            
            // Remove typing indicator
            removeTypingIndicator();
            
            // Update message content with error
            messageContent.innerHTML = 'Sorry, I encountered an error. Please try again.';
            
            // Re-enable input
            userInput.disabled = false;
            sendButton.disabled = false;
            userInput.focus();
        };
        
        // Send the message to the server using a separate fetch for the POST request
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message }),
        });
    }
    
    function addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', sender);
        
        const messageContent = document.createElement('div');
        messageContent.classList.add('message-content');
        
        // Process text for line breaks and URLs
        const processedText = processText(text);
        messageContent.innerHTML = processedText;
        
        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    function processText(text) {
        // Convert line breaks to <br>
        let processed = text.replace(/\n/g, '<br>');
        
        // Convert URLs to clickable links
        processed = processed.replace(
            /(https?:\/\/[^\s]+)/g, 
            '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
        );
        
        return processed;
    }
    
    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.classList.add('typing-indicator');
        typingDiv.id = 'typing-indicator';
        
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('span');
            typingDiv.appendChild(dot);
        }
        
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    function removeTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
});
