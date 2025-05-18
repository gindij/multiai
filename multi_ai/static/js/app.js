document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const promptInput = document.getElementById('prompt-input');
    const blendToggle = document.getElementById('blend-toggle');
    const detailsToggle = document.getElementById('details-toggle');
    const submitBtn = document.getElementById('submit-btn');
    const openaiSelect = document.getElementById('openai-model');
    const anthropicSelect = document.getElementById('anthropic-model');
    const geminiSelect = document.getElementById('gemini-model');
    const resultsContainer = document.getElementById('results-container');
    const loadingSpinner = document.getElementById('loading-spinner');
    const results = document.getElementById('results');
    const bestModelSpan = document.getElementById('best-model');
    const bestMethodSpan = document.getElementById('best-method');
    const bestResponseContent = document.getElementById('best-response-content');
    const allResponsesContainer = document.getElementById('all-responses-container');
    const allResponses = document.getElementById('all-responses');
    const themeToggle = document.getElementById('theme-toggle');
    const sunIcon = document.querySelector('.sun-icon');
    const moonIcon = document.querySelector('.moon-icon');

    // Configure marked.js for markdown rendering
    marked.setOptions({
        renderer: new marked.Renderer(),
        highlight: function(code, lang) {
            const language = hljs.getLanguage(lang) ? lang : 'plaintext';
            return hljs.highlight(code, { language }).value;
        },
        langPrefix: 'hljs language-',
        gfm: true,
        breaks: false
    });

    // Theme toggle functionality
    function initTheme() {
        console.log('Initializing theme');
        const prefersDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const savedTheme = localStorage.getItem('theme');

        if (savedTheme === 'dark' || (savedTheme === null && prefersDarkMode)) {
            console.log('Setting dark theme');
            document.body.classList.add('dark-theme');
            // Show sun icon (to switch to light mode)
            sunIcon.style.display = 'block';
            moonIcon.style.display = 'none';
            console.log('Icons: sun visible, moon hidden');
        } else {
            console.log('Setting light theme');
            document.body.classList.remove('dark-theme');
            // Show moon icon (to switch to dark mode)
            sunIcon.style.display = 'none';
            moonIcon.style.display = 'block';
            console.log('Icons: moon visible, sun hidden');
        }

        // Apply theme-aware syntax highlighting to any existing code blocks
        setTimeout(() => {
            document.querySelectorAll('pre code').forEach(block => {
                hljs.highlightElement(block);
            });
        }, 100);
    }

    function toggleTheme() {
        console.log('Toggle theme function called');

        // Force theme toggle to ensure it works
        const isDarkTheme = document.body.classList.contains('dark-theme');
        console.log('Current theme is dark:', isDarkTheme);

        if (isDarkTheme) {
            // Switch to light mode
            document.body.classList.remove('dark-theme');
            localStorage.setItem('theme', 'light');
            // Show moon icon (to switch to dark mode)
            sunIcon.style.display = 'none';
            moonIcon.style.display = 'block';
            console.log('THEME SWITCH - Now in light mode: moon icon visible, sun icon hidden');
            showNotification('Light mode activated');
            console.log('Switched to light mode');
        } else {
            // Switch to dark mode
            document.body.classList.add('dark-theme');
            localStorage.setItem('theme', 'dark');
            // Show sun icon (to switch to light mode)
            sunIcon.style.display = 'block';
            moonIcon.style.display = 'none';
            console.log('THEME SWITCH - Now in dark mode: sun icon visible, moon icon hidden');
            showNotification('Dark mode activated');
            console.log('Switched to dark mode');
        }

        // Add animation to theme toggle button
        themeToggle.classList.add('clicked');
        setTimeout(() => {
            themeToggle.classList.remove('clicked');
        }, 300);

        // Rehighlight code blocks to use theme-appropriate colors
        document.querySelectorAll('pre code').forEach(block => {
            hljs.highlightElement(block);
        });
    }

    // API Functions
    function fetchModels() {
        fetch('/models')
            .then(response => response.json())
            .then(data => {
                populateModelSelects(data.models);
            })
            .catch(error => {
                console.error('Error fetching models:', error);
                showNotification('Failed to load models', 'error');
            });
    }

    function populateModelSelects(models) {
        // Populate OpenAI models
        if (models.openai && models.openai.models) {
            populateSelect(openaiSelect, models.openai.models, models.openai.default);
        }

        // Populate Anthropic models
        if (models.anthropic && models.anthropic.models) {
            populateSelect(anthropicSelect, models.anthropic.models, models.anthropic.default);
        }

        // Populate Gemini models
        if (models.gemini && models.gemini.models) {
            populateSelect(geminiSelect, models.gemini.models, models.gemini.default);
        }
    }

    function populateSelect(selectElement, models, defaultModel) {
        selectElement.innerHTML = '';

        models.forEach(model => {
            const option = document.createElement('option');
            option.value = model.id;
            option.textContent = model.name;

            if (model.id === defaultModel) {
                option.selected = true;
            }

            selectElement.appendChild(option);
        });
    }

    // Form submission
    function submitPrompt() {
        const prompt = promptInput.value.trim();

        if (!prompt) {
            showNotification('Please enter a prompt', 'error');
            return;
        }

        // Show loading state
        resultsContainer.classList.remove('hidden');
        loadingSpinner.style.display = 'flex';
        results.style.display = 'none';

        // Prepare request data
        const requestData = {
            prompt: prompt,
            blend: blendToggle.checked,
            include_details: detailsToggle.checked,
            models: {
                openai: openaiSelect.value,
                anthropic: anthropicSelect.value,
                gemini: geminiSelect.value
            }
        };

        // Send API request
        fetch('/compare', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            displayResults(data);
            showNotification('Responses received!', 'success');
        })
        .catch(error => {
            console.error('Error comparing models:', error);
            showNotification('An error occurred', 'error');
        })
        .finally(() => {
            loadingSpinner.style.display = 'none';
            results.style.display = 'block';
        });
    }

    // Render markdown
    function renderMarkdown(content) {
        try {
            return marked.parse(content);
        } catch (e) {
            console.error('Error parsing markdown:', e);
            return content;
        }
    }

    // Display results
    function displayResults(data) {
        if (data.success && data.result) {
                // Render and highlight best response
                bestResponseContent.innerHTML = renderMarkdown(data.result);
                bestResponseContent.querySelectorAll('pre code').forEach(block => {
                    hljs.highlightElement(block);
                });
    
                // Get explanation element
                const judgeExplanation = document.getElementById('judge-explanation');
    
                // Show model metadata
                if (data.details) {
                    if (data.details.best_response) {
                        bestModelSpan.textContent = `Model: ${data.details.best_response.provider} (${data.details.best_response.model})`;
                    }
    
                    if (data.details.method) {
                        bestMethodSpan.textContent = `Method: ${data.details.method}`;
                    }
    
                    // Show judge explanation
                    
                    // Initialize to visible
                    judgeExplanation.style.display = 'block';
    
                    // Prepare content for explanation
                    let explanationContent = '';
                    
                    // Check for explanation in different locations
                    if (data.explanation) {
                        // Check for explanation at top level first
                        explanationContent = `<p>${data.explanation}</p>`;
                    } else if (data.details && data.details.explanation) {
                        // Fallback to checking details object
                        explanationContent = `<p>${data.details.explanation}</p>`;
                    } else {
                        // No explanation found, use fallback based on method
                        if (data.details && data.details.method) {
                            
                            if (data.details.method === 'blend') {
                                explanationContent = `<p>Response created by blending models based on quality assessment.</p>`;
                            } else if (data.details.method === 'single') {
                                explanationContent = `<p>Only one model response was available.</p>`;
                            } else if (data.details.method === 'select' || data.details.method === 'fallback') {
                                const reasonText = data.details.reason ? data.details.reason : 'quality assessment';
                                explanationContent = `<p>The judge selected this response based on ${reasonText}.</p>`;
                            } else {
                                explanationContent = `<p>Response selected based on quality assessment.</p>`;
                            }
                        } else {
                            explanationContent = `<p>Response selected based on quality assessment.</p>`;
                        }
                    }
    
                    // If we're in blend mode, add weight breakdown
                    if (data.details.method === 'blend' && data.details.weights && data.details.responses) {
                        const weightBreakdown = createBlendExplanation(data.details.responses, data.details.weights);
                        explanationContent += weightBreakdown;
                    }
    
                    // Set the content
                    if (explanationContent) {
                        judgeExplanation.innerHTML = explanationContent;
                    } else {
                        judgeExplanation.style.display = 'none';
                    }

                    // Display all responses if available
                    if (data.details.all_responses || data.details.responses) {
                        const responses = data.details.all_responses || data.details.responses;
                        displayAllResponses(responses, data.details.weights);
                    } else {
                        allResponsesContainer.style.display = 'none';
                    }
                } else {
                    bestModelSpan.textContent = 'Model: Best selected';
                    bestMethodSpan.textContent = '';
                    judgeExplanation.style.display = 'none';
                    allResponsesContainer.style.display = 'none';
                }
            } else {
                bestResponseContent.textContent = 'Failed to get responses. Please try again.';
                bestModelSpan.textContent = '';
                bestMethodSpan.textContent = '';
                document.getElementById('judge-explanation').style.display = 'none';
                allResponsesContainer.style.display = 'none';
            }
        } catch (err) {
            console.error('Error displaying results:', err);
            bestResponseContent.textContent = 'An error occurred while displaying results.';
            showNotification('Error displaying results', 'error');
        }
    }

    // Create blend weight breakdown HTML
    function createBlendExplanation(responses, weights) {
        if (!responses || !weights || responses.length !== weights.length) {
            return '';
        }

        // Format weights as percentages with model names
        const weightStrings = responses.map((response, index) => {
            const percentage = Math.round(weights[index] * 100);
            return `<span class="weight-indicator">${response.provider} (${response.model}): <strong>${percentage}%</strong></span>`;
        });

        // Join with commas and 'and' for the last item
        let weightText;
        if (weightStrings.length === 2) {
            weightText = weightStrings.join(' and ');
        } else if (weightStrings.length > 2) {
            const lastItem = weightStrings.pop();
            weightText = weightStrings.join(', ') + ', and ' + lastItem;
        } else {
            weightText = weightStrings[0];
        }

        return `<div class="weight-breakdown">Weight distribution: ${weightText}</div>`;
    }

    // Display all responses
    function displayAllResponses(responses, weights) {
        allResponsesContainer.style.display = 'block';
        allResponses.innerHTML = '';

        responses.forEach((response, index) => {
            const card = document.createElement('div');
            card.className = 'response-card';

            const header = document.createElement('h4');
            header.textContent = `${response.provider} (${response.model})`;

            // Add weight if available
            if (weights && weights[index] !== undefined) {
                const weightSpan = document.createElement('span');
                weightSpan.className = 'response-weight';
                weightSpan.textContent = `Weight: ${Math.round(weights[index] * 100)}%`;
                header.appendChild(weightSpan);
            }

            const content = document.createElement('div');
            content.className = 'response-card-content markdown-content';
            content.innerHTML = renderMarkdown(response.response);

            // Apply syntax highlighting
            content.querySelectorAll('pre code').forEach(block => {
                hljs.highlightElement(block);
            });

            card.appendChild(header);
            card.appendChild(content);
            allResponses.appendChild(card);
        });
    }

    // Notification system
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;

        document.body.appendChild(notification);

        // Animate in
        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateY(0)';
        }, 10);

        // Remove after delay
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateY(10px)';

            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }

    // Attach event listeners
    themeToggle.addEventListener('click', function(e) {
        e.preventDefault();
        console.log('Theme toggle clicked');
        toggleTheme();
    });

    submitBtn.addEventListener('click', submitPrompt);

    // Handle Enter + Ctrl in textarea
    promptInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && e.ctrlKey) {
            e.preventDefault();
            submitPrompt();
        }
    });

    // Initialize
    initTheme();
    fetchModels();
});