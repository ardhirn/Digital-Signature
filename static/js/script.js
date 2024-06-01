document.addEventListener('DOMContentLoaded', function() {
    var methodSelect = document.getElementById('method');
    var codeInput = document.getElementById('code-input');
    var qrInput = document.getElementById('qr-input');
    var verificationResult = document.getElementById('verification-result');
    var pdfPreview = document.getElementById('pdf-preview');
    var pdfFrame = document.getElementById('pdf-frame');
    var downloadLink = document.getElementById('download-link');

    function toggleInput() {
        if (methodSelect.value === 'code') {
            codeInput.style.display = 'block';
            qrInput.style.display = 'none';
        } else {
            codeInput.style.display = 'none';
            qrInput.style.display = 'block';
        }
    }

    methodSelect.addEventListener('change', toggleInput);
    toggleInput();  // Set initial state

    document.querySelector('form').addEventListener('submit', function(event) {
        event.preventDefault();
        var formData = new FormData(event.target);
        fetch('/verify', {
            method: 'POST',
            body: formData
        }).then(response => response.json())
        .then(data => {
            if (data.status === 'valid') {
                verificationResult.textContent = 'Document is valid!';
                pdfPreview.style.display = 'block';
                pdfFrame.src = '/preview/' + data.filename;
                downloadLink.href = '/download/' + data.filename;
            } else {
                verificationResult.textContent = 'Document is invalid!';
                pdfPreview.style.display = 'none';
            }
        }).catch(error => {
            verificationResult.textContent = 'An error occurred during verification.';
            pdfPreview.style.display = 'none';
        });
    });
});
