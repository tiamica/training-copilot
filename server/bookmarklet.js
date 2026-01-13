javascript:(function(){
  // Configuration
  const CONFIG = {
    PROXY_URL: "http://localhost:3000/api/generate",
    MODEL: "llama2",
    THEME: "dark"
  };
  
  // State
  let recordedPages = JSON.parse(localStorage.getItem('training_pages') || '[]');
  let widget = null;
  
  // Create UI
  function createUI() {
    if (widget && document.body.contains(widget)) {
      widget.remove();
      widget = null;
      return;
    }
    
    widget = document.createElement('div');
    widget.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      width: 320px;
      background: ${CONFIG.THEME === 'dark' ? '#1a202c' : 'white'};
      color: ${CONFIG.THEME === 'dark' ? 'white' : 'black'};
      border: 2px solid #4299e1;
      border-radius: 8px;
      box-shadow: 0 4px 6px rgba(0,0,0,0.1);
      z-index: 10000;
      font-family: Arial, sans-serif;
      font-size: 14px;
    `;
    
    widget.innerHTML = `
      <div style="padding: 15px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
          <h3 style="margin: 0; color: #63b3ed;">🤖 Training Copilot</h3>
          <button id="close-btn" style="background: none; border: none; color: #a0aec0; cursor: pointer; font-size: 20px;">×</button>
        </div>
        
        <div style="background: #2d3748; padding: 10px; border-radius: 5px; margin-bottom: 15px;">
          <div>📝 Recorded: <strong>${recordedPages.length}</strong> pages</div>
          <div>🤖 AI: <span id="ai-status">Ready</span></div>
        </div>
        
        <div style="margin-bottom: 15px;">
          <button id="record-btn" style="width: 100%; padding: 10px; background: #48bb78; color: white; border: none; border-radius: 5px; cursor: pointer; margin-bottom: 10px;">
            🎬 Record This Page
          </button>
          
          <div style="display: flex; gap: 10px;">
            <button id="hint-btn" style="flex: 1; padding: 10px; background: #4299e1; color: white; border: none; border-radius: 5px; cursor: pointer;">
              🤖 Get Hint
            </button>
            <button id="auto-btn" style="flex: 1; padding: 10px; background: #ed8936; color: white; border: none; border-radius: 5px; cursor: pointer;">
              ⚡ Auto-Answer
            </button>
          </div>
        </div>
        
        <div style="background: #2d3748; padding: 10px; border-radius: 5px; margin-bottom: 15px;">
          <div style="font-size: 12px; color: #a0aec0;">
            <div>Proxy: ${CONFIG.PROXY_URL}</div>
            <div>Model: ${CONFIG.MODEL}</div>
          </div>
        </div>
        
        <div id="results" style="max-height: 200px; overflow-y: auto;"></div>
      </div>
    `;
    
    document.body.appendChild(widget);
    
    // Add event listeners
    document.getElementById('close-btn').onclick = () => widget.remove();
    document.getElementById('record-btn').onclick = recordPage;
    document.getElementById('hint-btn').onclick = () => processAssessment('hint');
    document.getElementById('auto-btn').onclick = () => processAssessment('auto');
  }
  
  // Record page content
  function recordPage() {
    const pageData = {
      url: window.location.href,
      title: document.title,
      content: document.body.innerText.substring(0, 5000),
      timestamp: new Date().toISOString()
    };
    
    recordedPages.push(pageData);
    localStorage.setItem('training_pages', JSON.stringify(recordedPages));
    
    alert(`Page recorded! Total: ${recordedPages.length}`);
  }
  
  // Call AI
  async function callAI(prompt) {
    try {
      document.getElementById('ai-status').textContent = 'Processing...';
      
      const response = await fetch(CONFIG.PROXY_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: CONFIG.MODEL,
          prompt: prompt,
          stream: false
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.error) {
        throw new Error(data.message || 'AI error');
      }
      
      document.getElementById('ai-status').textContent = 'Ready';
      return data.response || '';
      
    } catch (error) {
      document.getElementById('ai-status').textContent = 'Error';
      console.error('AI Error:', error);
      alert(`AI Error: ${error.message}`);
      return null;
    }
  }
  
  // Process assessment
  async function processAssessment(mode) {
    // Check if on assessment page
    const hasQuestions = document.querySelector('input[type="radio"], input[type="checkbox"]') !== null;
    
    if (!hasQuestions) {
      alert('No questions found on this page.');
      return;
    }
    
    // Extract questions
    const questions = extractQuestions();
    
    if (questions.length === 0) {
      alert('Could not find any questions.');
      return;
    }
    
    // Get training content
    const trainingContent = recordedPages.map(p => p.content).join('\n\n');
    
    // Process each question
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '<div style="color: #a0aec0;">Processing questions...</div>';
    
    for (let i = 0; i < Math.min(questions.length, 5); i++) { // Limit to 5 questions
      const question = questions[i];
      
      const prompt = mode === 'hint' 
        ? `Based on this training: ${trainingContent.substring(0, 2000)}\n\nQuestion: ${question.text}\n\nProvide a helpful hint (not the answer):`
        : `Based on this training: ${trainingContent.substring(0, 2000)}\n\nQuestion: ${question.text}\n\nAnswer with just the letter (A, B, C, or D):`;
      
      const answer = await callAI(prompt);
      
      if (answer) {
        resultsDiv.innerHTML += `
          <div style="background: #4a5568; padding: 10px; margin: 5px 0; border-radius: 5px;">
            <strong>Q${i+1}:</strong> ${question.text.substring(0, 100)}...
            <div style="color: #90cdf4;">AI: ${answer}</div>
          </div>
        `;
        
        // For auto mode, try to select answer
        if (mode === 'auto' && question.options) {
          const match = answer.match(/[A-D]/i);
          if (match) {
            const letter = match[0].toUpperCase();
            const optionIndex = letter.charCodeAt(0) - 65; // A=0, B=1, etc.
            if (optionIndex < question.options.length) {
              question.options[optionIndex].checked = true;
            }
          }
        }
      }
      
      // Small delay between requests
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    resultsDiv.innerHTML += '<div style="color: #48bb78; margin-top: 10px;">✅ Processing complete!</div>';
  }
  
  // Extract questions from page
  function extractQuestions() {
    const questions = [];
    const inputs = document.querySelectorAll('input[type="radio"], input[type="checkbox"]');
    
    // Group by name
    const groups = {};
    inputs.forEach(input => {
      const name = input.name || 'question_' + Math.random();
      if (!groups[name]) groups[name] = [];
      groups[name].push(input);
    });
    
    // Create question objects
    Object.values(groups).forEach((inputs, index) => {
      const firstInput = inputs[0];
      const container = firstInput.closest('div, li, tr, p') || firstInput.parentElement;
      
      questions.push({
        id: index,
        text: container.innerText.substring(0, 500) || `Question ${index + 1}`,
        options: inputs,
        container: container
      });
    });
    
    return questions;
  }
  
  // Initialize
  try {
    createUI();
    console.log('Training Copilot loaded successfully!');
  } catch (error) {
    console.error('Failed to load Training Copilot:', error);
    alert('Training Copilot failed to load. Check console for details.');
  }
})();
