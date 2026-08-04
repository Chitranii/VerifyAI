// Get saved result — try localStorage first, then sessionStorage
const raw = localStorage.getItem('verifyResult') ||
            sessionStorage.getItem('verifyResult');

if (!raw) {
    window.location.href = '/';
}

const data     = JSON.parse(raw);
const analysis = data.analysis;

// Parse AI response text
function parseAnalysis(text) {
    const result = {
        verdict:    'UNKNOWN',
        confidence: '0',
        summary:    '',
        checks:     []
    };

    // RESULT
    const resultMatch = text.match(/RESULT:\s*(AUTHENTIC|SUSPICIOUS|REJECTED)/i);
    if (resultMatch) {
        result.verdict = resultMatch[1].toUpperCase();
    }

    // CONFIDENCE
    const confMatch = text.match(/CONFIDENCE:\s*(\d+)/i);
    if (confMatch) {
        result.confidence = confMatch[1];
    }

    // SUMMARY
    const summaryMatch = text.match(/SUMMARY:\s*(.+)/i);
    if (summaryMatch) {
        result.summary = summaryMatch[1].trim();
    }

    // CHECKS
    const checkLines = text.match(/- .+/gi);
    if (checkLines) {
        checkLines.forEach(line => {
            const parts = line.match(/- (.+): (PASS|FAIL|WARN)\s*[—-]\s*(.+)/i);
            if (parts) {
                result.checks.push({
                    name:   parts[1].trim(),
                    status: parts[2].toUpperCase(),
                    reason: parts[3].trim()
                });
            }
        });
    }

    return result;
}

const parsed = parseAnalysis(analysis);

// DOM references
const resultBox     = document.getElementById('resultBox');
const resultIcon    = document.getElementById('resultIcon');
const resultTitle   = document.getElementById('resultTitle');
const resultSubtitle= document.getElementById('resultSubtitle');
const resultSummary = document.getElementById('resultSummary');
const checksGrid    = document.getElementById('checksGrid');
const confidenceNum = document.getElementById('confidenceNum');
const confidenceBar = document.getElementById('confidenceBar');

// Verdict styling
if (parsed.verdict === 'AUTHENTIC') {
    resultBox.classList.add('authentic');
    resultIcon.textContent  = '✓';
    resultTitle.textContent = 'Document Authentic';
} else if (parsed.verdict === 'SUSPICIOUS') {
    resultBox.classList.add('suspicious');
    resultIcon.textContent  = '!';
    resultTitle.textContent = 'Review Required';
} else {
    resultBox.classList.add('rejected');
    resultIcon.textContent  = '✕';
    resultTitle.textContent = 'Document Rejected';
}

// Subtitle and summary
resultSubtitle.textContent = parsed.confidence + '% confidence · ' + data.doc_type;
resultSummary.textContent  = parsed.summary;

// Animate confidence ring
const conf = parseInt(parsed.confidence) || 0;
const circumference = 339.29;
requestAnimationFrame(() => {
    setTimeout(() => {
        confidenceBar.style.strokeDashoffset = circumference * (1 - conf / 100);
    }, 100);
});

// Animate confidence number
let current = 0;
const confInterval = setInterval(() => {
    current += Math.max(1, Math.round(conf / 40));
    if (current >= conf) {
        current = conf;
        clearInterval(confInterval);
    }
    confidenceNum.textContent = current + '%';
}, 30);

// Render checks
parsed.checks.forEach((check, index) => {
    const div       = document.createElement('div');
    div.className   = 'check-item ' + check.status.toLowerCase();
    div.style.animationDelay = (index * 0.1) + 's';
    div.innerHTML   = `
        <div class="check-status">${check.status}</div>
        <div class="check-detail">
            <div class="check-name">${check.name}</div>
            <div class="check-reason">${check.reason}</div>
        </div>
    `;
    checksGrid.appendChild(div);
});

// Launch confetti for authentic results
if (parsed.verdict === 'AUTHENTIC' && typeof launchConfetti === 'function') {
    launchConfetti();
}

// Clear storage after displaying
localStorage.removeItem('verifyResult');
sessionStorage.removeItem('verifyResult');
