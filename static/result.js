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

// Render checks
parsed.checks.forEach(check => {
    const div       = document.createElement('div');
    div.className   = 'check-item ' + check.status.toLowerCase();
    div.innerHTML   = `
        <div class="check-status">${check.status}</div>
        <div class="check-detail">
            <div class="check-name">${check.name}</div>
            <div class="check-reason">${check.reason}</div>
        </div>
    `;
    checksGrid.appendChild(div);
});

// Clear storage after displaying
localStorage.removeItem('verifyResult');
sessionStorage.removeItem('verifyResult');