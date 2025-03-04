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
                
                // Store citation data if available
                if (data.citations) {
                    currentCitations = data.citations;
                    console.log("Received citations:", currentCitations);
                    
                    // Reprocess the entire message content to apply citations
                    const fullText = messageContent.innerHTML;
                    messageContent.innerHTML = processText(fullText);
                }
                
                // Re-enable input
                userInput.disabled = false;
                sendButton.disabled = false;
                userInput.focus();
                return;
            }
            
            if (data.chunk) {
                // Only process for line breaks and URLs, not citations
                let processedChunk = data.chunk.replace(/\n/g, '<br>');
                
                // Convert URLs to clickable links
                processedChunk = processedChunk.replace(
                    /(https?:\/\/[^\s]+)/g, 
                    '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
                );
                
                // Append the chunk to the message
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
    
    // Store citation data for the current response
    let currentCitations = [];
    
    function processText(text) {
        // Convert line breaks to <br>
        let processed = text.replace(/\n/g, '<br>');
        
        // Convert URLs to clickable links
        processed = processed.replace(
            /(https?:\/\/[^\s]+)/g, 
            '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
        );
        
        // Only process citations if we have citation data
        if (currentCitations.length > 0) {
            console.log("Processing citations for text:", processed);
            
            // Create a temporary div to parse the HTML
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = processed;
            
            // Get the text content
            const textContent = tempDiv.textContent;
            
            // Find all citation patterns in the text content
            const citationRegex = /\[+(\d+)\]+/g;
            let match;
            const matches = [];
            
            while ((match = citationRegex.exec(textContent)) !== null) {
                matches.push({
                    fullMatch: match[0],
                    number: parseInt(match[1]),
                    index: match.index
                });
            }
            
            console.log("Found citation matches:", matches);
            
            // If we found matches, create a new HTML string with the citations replaced
            if (matches.length > 0) {
                let newHtml = '';
                let lastIndex = 0;
                
                for (const match of matches) {
                    // Add the text before this match
                    newHtml += textContent.substring(lastIndex, match.index);
                    
                    // Add the citation span
                    const citation = currentCitations.find(c => c.number === match.number);
                    const citationText = citation ? citation.text : 'Citation not found';
                    newHtml += `<span class="citation" data-citation-text="${citationText}">[${match.number}]</span>`;
                    
                    // Update the last index
                    lastIndex = match.index + match.fullMatch.length;
                }
                
                // Add any remaining text
                newHtml += textContent.substring(lastIndex);
                
                // Use the new HTML
                processed = newHtml;
                
                console.log("Processed text with citations:", processed);
            }
        }
        
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
