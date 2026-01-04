console.log("✅ theme.js loaded");

// Make toggleTheme available globally
window.toggleTheme = function() {
    const current = document.documentElement.dataset.theme || "light";
    const newTheme = current === "dark" ? "light" : "dark";
    applyTheme(newTheme);
    localStorage.setItem("theme", newTheme);
    updateThemeButton(newTheme);
    console.log("🔄 Theme toggled to:", newTheme);
}

// Theme management
function initTheme() {
    const saved = localStorage.getItem("theme") || "light"; // DEFAULT: light
    applyTheme(saved);
    updateThemeButton(saved);
    console.log("🎨 Theme initialized:", saved);
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
}

function updateThemeButton(theme) {
    const icon = document.getElementById("themeIcon");
    const text = document.getElementById("themeText");
    
    if (!icon || !text) return;
    
    if (theme === "dark") {
        icon.textContent = "☀️";
        text.textContent = "Modo Claro";
    } else {
        icon.textContent = "🌙";
        text.textContent = "Modo Oscuro";
    }
}

// Initialize on load
document.addEventListener("DOMContentLoaded", initTheme);
