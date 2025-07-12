document.addEventListener('DOMContentLoaded', function() {
    // Автоматический вход при наличии кода
    const savedCode = localStorage.getItem('telegram_access_code');
    if (savedCode && window.location.pathname === '/') {
        checkAccessCode(savedCode);
    }

    // Проверка авторизации на других страницах
    if (window.location.pathname !== '/' && !localStorage.getItem('telegram_access_code')) {
        window.location.href = '/';
    }
});

function checkAccessCode(code) {
    fetch(`/check_access_code?code=${code}`)
        .then(response => response.json())
        .then(data => {
            if (data.valid) {
                window.location.href = `/groups/${code}`;
            } else {
                localStorage.removeItem('telegram_access_code');
            }
        });
}