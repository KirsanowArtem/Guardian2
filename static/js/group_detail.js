document.addEventListener('DOMContentLoaded', function() {
    const groupId = window.location.pathname.split('/')[2];

    // Загрузка участников
    fetch(`/api/group/${groupId}/members`)
        .then(response => response.json())
        .then(data => {
            const container = document.querySelector('.members-list');
            container.innerHTML = '';

            data.members.forEach(member => {
                const memberCard = document.createElement('div');
                memberCard.className = 'member-card';
                memberCard.innerHTML = `
                    <img src="${member.avatar || '/static/img/default-user.png'}" class="member-avatar">
                    <div class="member-info">
                        <h3>${member.name}</h3>
                        <p>@${member.username || 'нет username'}</p>
                        <p>ID: ${member.id}</p>
                    </div>
                    <div class="member-actions">
                        <button class="btn action-btn mute-btn" data-user-id="${member.id}">Мут</button>
                        <button class="btn action-btn ban-btn" data-user-id="${member.id}">Бан</button>
                    </div>
                `;
                container.appendChild(memberCard);
            });
        });

    // Обработка вкладок
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.tab-btn, .tab-content').forEach(el => {
                el.classList.remove('active');
            });
            this.classList.add('active');
            document.getElementById(`${this.dataset.tab}-tab`).classList.add('active');
        });
    });
});