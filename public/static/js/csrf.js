(() => {
    const meta = document.querySelector('meta[name="csrf-token"]');
    const token = meta ? meta.content : '';

    document.addEventListener('DOMContentLoaded', () => {
        if (!token) return;
        document.querySelectorAll('form').forEach((form) => {
            const method = (form.getAttribute('method') || 'GET').toUpperCase();
            if (!['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) return;
            if (form.querySelector('input[name="_csrf_token"]')) return;
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = '_csrf_token';
            input.value = token;
            form.appendChild(input);
        });
    });

    if (!token || typeof window.fetch !== 'function') return;
    const originalFetch = window.fetch.bind(window);
    window.fetch = (resource, options = {}) => {
        const method = (options.method || 'GET').toUpperCase();
        if (!['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
            return originalFetch(resource, options);
        }

        const requestUrl = typeof resource === 'string' ? resource : resource.url;
        const url = new URL(requestUrl, window.location.href);
        if (url.origin !== window.location.origin) {
            return originalFetch(resource, options);
        }

        const headers = new Headers(options.headers || {});
        headers.set('X-CSRFToken', token);
        return originalFetch(resource, { ...options, headers });
    };
})();
