const uploadZone = document.getElementById('uploadZone');
const fileInput  = document.getElementById('fileInput');
const fileInfo   = document.getElementById('fileInfo');
const fileName   = document.getElementById('fileName');
const verifyBtn  = document.getElementById('verifyBtn');
const uploadForm = document.getElementById('uploadForm');

// Click upload zone
uploadZone.addEventListener('click', () => {
    fileInput.click();
});

// File selected
fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
        const file = fileInput.files[0];
        if (file.size > 900 * 1024) {
            alert('File too large! Please upload under 900KB.\nTip: Take a screenshot of the document instead of a direct photo.');
            removeFile();
            return;
        }
        showFile(file);
    }
});

// Drag over
uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('dragover');
});

// Drag leave
uploadZone.addEventListener('dragleave', () => {
    uploadZone.classList.remove('dragover');
});

// Drop file
uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file) {
        if (file.size > 900 * 1024) {
            alert('File too large! Please upload under 900KB.');
            return;
        }
        fileInput.files = e.dataTransfer.files;
        showFile(file);
    }
});

// Show selected file
function showFile(file) {
    fileName.textContent    = '📄 ' + file.name;
    fileInfo.style.display  = 'flex';
    verifyBtn.disabled      = false;
}

// Remove file
function removeFile() {
    fileInput.value         = '';
    fileInfo.style.display  = 'none';
    verifyBtn.disabled      = true;
}

// Form submit
uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    if (!fileInput.files.length) {
        alert('Please select a file.');
        return;
    }

    verifyBtn.textContent = 'Analysing document...';
    verifyBtn.disabled    = true;

    const formData = new FormData(uploadForm);

    try {
        const response = await fetch('/verify', {
            method: 'POST',
            body:   formData
        });

        const result = await response.json();

        if (result.success) {
            // Save with fallback for mobile browsers
            try {
                localStorage.setItem('verifyResult', JSON.stringify(result));
            } catch(e) {
                sessionStorage.setItem('verifyResult', JSON.stringify(result));
            }
            window.location.href = '/result';

        } else {
            alert('Error: ' + result.error);
            verifyBtn.textContent = 'Verify Document — ₹40';
            verifyBtn.disabled    = false;
        }

    } catch (error) {
        console.error(error);
        alert('Upload failed. Please try again.');
        verifyBtn.textContent = 'Verify Document — ₹40';
        verifyBtn.disabled    = false;
    }
});