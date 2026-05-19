// API base URL — overridden at build time on Render (see build.sh)
window.API_BASE = window.API_BASE || (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' ? 'http://localhost:8000' : '');
