// Copiloto de Supervivencia Financiera - JavaScript
console.log("✅ app.js loaded");

document.addEventListener('DOMContentLoaded', function() {
    
    // Form validation
    const analysisForm = document.querySelector('.analysis-form');
    if (analysisForm) {
        analysisForm.addEventListener('submit', function(e) {
            const submitButton = this.querySelector('button[type="submit"]');
            submitButton.disabled = true;
            submitButton.textContent = '⏳ Analizando...';
        });
    }

    // File input labels
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const fileName = this.files[0]?.name;
            const label = this.previousElementSibling;
            if (fileName && label) {
                const small = document.createElement('small');
                small.textContent = `Archivo: ${fileName}`;
                small.style.display = 'block';
                small.style.color = '#4caf50';
                small.style.marginTop = '0.3rem';
                
                // Remove previous filename display
                const existingSmall = label.nextElementSibling;
                if (existingSmall && existingSmall.textContent.startsWith('Archivo:')) {
                    existingSmall.remove();
                }
                
                label.after(small);
            }
        });
    });

    // Credit line auto-validation
    const creditTotal = document.getElementById('credit_line_total');
    const creditUsed = document.getElementById('credit_line_used');
    
    if (creditUsed && creditTotal) {
        creditUsed.addEventListener('input', function() {
            const total = parseFloat(creditTotal.value) || 0;
            const used = parseFloat(this.value) || 0;
            
            if (used > total && total > 0) {
                this.setCustomValidity('El crédito usado no puede ser mayor que el total');
            } else {
                this.setCustomValidity('');
            }
        });
    }

    // Auto-dismiss alerts
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transition = 'opacity 0.5s';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

    // Table row highlighting
    const tables = document.querySelectorAll('table tbody tr');
    tables.forEach(row => {
        row.addEventListener('click', function() {
            this.style.backgroundColor = '#e3f2fd';
            setTimeout(() => {
                this.style.backgroundColor = '';
            }, 300);
        });
    });

    // Refine form validation
    const refineForm = document.querySelector('.refine-form');
    if (refineForm) {
        refineForm.addEventListener('submit', function(e) {
            const checkboxes = this.querySelectorAll('input[type="checkbox"][name="priorities"]:checked');
            const timing = this.querySelector('select[name="timing"]').value;
            const control = this.querySelector('input[name="control"]:checked');
            
            // At least one field should be filled
            if (checkboxes.length === 0 && !timing && !control) {
                e.preventDefault();
                alert('Por favor, responde al menos una pregunta para refinar el informe.');
                return false;
            }
            
            const submitButton = this.querySelector('button[type="submit"]');
            submitButton.disabled = true;
            submitButton.textContent = '⏳ Actualizando...';
        });
    }

    // Format numbers in tables
    const numberCells = document.querySelectorAll('td');
    numberCells.forEach(cell => {
        const text = cell.textContent.trim();
        if (text.match(/^-?\d+(\.\d{2})?€$/)) {
            const num = parseFloat(text.replace('€', ''));
            cell.textContent = num.toLocaleString('es-ES', { 
                minimumFractionDigits: 2,
                maximumFractionDigits: 2 
            }) + '€';
        }
    });

    // Console welcome message
    console.log('%c💰 Copiloto de Supervivencia Financiera', 
                'font-size: 20px; font-weight: bold; color: #667eea;');
    console.log('%cPowered by Python + Flask + Claude 4.5', 
                'font-size: 12px; color: #666;');
    console.log('%cAnálisis determinista con interpretación IA', 
                'font-size: 12px; color: #666;');
});
