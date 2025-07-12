document.addEventListener('DOMContentLoaded', function() {
    // Переключение вкладок
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn, .tab-content').forEach(el => {
                el.classList.remove('active');
            });
            btn.classList.add('active');
            document.getElementById(`${btn.dataset.tab}-tab`).classList.add('active');
        });
    });

    // Обработка действий с пользователями
    document.querySelectorAll('.mute-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const duration = prompt('Введите продолжительность мута в минутах:', '60');
            if (duration) {
                const reason = prompt('Введите причину мута:', 'Нарушение правил');
                const response = await fetch(`/api/user/${btn.dataset.userId}/mute`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        duration: parseInt(duration) * 60,
                        reason: reason
                    })
                });
                if (response.ok) {
                    alert('Пользователь замьючен');
                }
            }
        });
    });
});