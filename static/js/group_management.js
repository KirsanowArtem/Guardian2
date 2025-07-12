document.addEventListener('DOMContentLoaded', function() {
    // Элементы модальных окон
    const muteModal = document.getElementById('mute-modal');
    const banModal = document.getElementById('ban-modal');

    // Текущие выбранные пользователь и группа
    let currentUserId = null;
    const groupId = window.location.pathname.split('/')[2];

    // Обработчики кнопок мута
    document.querySelectorAll('.mute-user').forEach(btn => {
        btn.addEventListener('click', function() {
            currentUserId = this.dataset.userId;
            document.getElementById('mute-reason').value = '';
            document.getElementById('mute-duration').value = '3600';
            muteModal.style.display = 'block';
        });
    });

    document.querySelectorAll('.unmute-user').forEach(btn => {
        btn.addEventListener('click', function() {
            currentUserId = this.dataset.userId;
            unmuteUser(currentUserId);
        });
    });

    // Обработчики кнопок бана
    document.querySelectorAll('.ban-user').forEach(btn => {
        btn.addEventListener('click', function() {
            currentUserId = this.dataset.userId;
            document.getElementById('ban-reason').value = '';
            banModal.style.display = 'block';
        });
    });

    document.querySelectorAll('.unban-user').forEach(btn => {
        btn.addEventListener('click', function() {
            currentUserId = this.dataset.userId;
            unbanUser(currentUserId);
        });
    });

    // Подтверждение мута
    document.getElementById('confirm-mute').addEventListener('click', function() {
        const reason = document.getElementById('mute-reason').value;
        const duration = document.getElementById('mute-duration').value;

        fetch('/api/mute_user', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                group_id: groupId,
                user_id: currentUserId,
                reason: reason,
                duration: duration
            })
        }).then(response => {
            if (response.ok) {
                location.reload();
            }
        });

        muteModal.style.display = 'none';
    });

    // Подтверждение бана
    document.getElementById('confirm-ban').addEventListener('click', function() {
        const reason = document.getElementById('ban-reason').value;

        fetch('/api/ban_user', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                group_id: groupId,
                user_id: currentUserId,
                reason: reason
            })
        }).then(response => {
            if (response.ok) {
                location.reload();
            }
        });

        banModal.style.display = 'none';
    });

    // Отмена действий
    document.getElementById('cancel-mute').addEventListener('click', function() {
        muteModal.style.display = 'none';
    });

    document.getElementById('cancel-ban').addEventListener('click', function() {
        banModal.style.display = 'none';
    });

    // Закрытие модальных окон при клике вне их
    window.addEventListener('click', function(event) {
        if (event.target === muteModal) {
            muteModal.style.display = 'none';
        }
        if (event.target === banModal) {
            banModal.style.display = 'none';
        }
    });

    // Функция размута пользователя
    function unmuteUser(userId) {
        fetch('/api/unmute_user', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                group_id: groupId,
                user_id: userId
            })
        }).then(response => {
            if (response.ok) {
                location.reload();
            }
        });
    }

    // Функция разбана пользователя
    function unbanUser(userId) {
        fetch('/api/unban_user', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                group_id: groupId,
                user_id: userId
            })
        }).then(response => {
            if (response.ok) {
                location.reload();
            }
        });
    }
});