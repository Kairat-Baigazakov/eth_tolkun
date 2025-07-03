document.addEventListener('DOMContentLoaded', function () {
    const modal = new bootstrap.Modal(document.getElementById('placementModal'));
    const modalForm = document.getElementById('modal-form');
    const modalFields = document.getElementById('modal-fields');

    let editingRoomId = null;
    let roomCapacity = 0;
    let currentValues = [];

    // При клике "Изменить"
    document.querySelectorAll('.edit-room-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            editingRoomId = btn.dataset.roomId;
            // Найти данные о комнате
            const room = window.roomsData.find(r => String(r.id) === String(editingRoomId));
            roomCapacity = room.capacity;

            // Какие гости уже размещены в этой комнате?
            currentValues = room.placements.slice();
            while (currentValues.length < roomCapacity) currentValues.push("");

            drawModalFields();

            modal.show();
        });
    });

    function drawModalFields() {
        modalFields.innerHTML = '';
        // Список доступных гостей + уже выбранные в этой комнате (для выбора/замены)
        let available = window.availableGuests.map(g => g.fio);

        for (let i = 0; i < roomCapacity; i++) {
            // Уже выбранный в этом поле
            let selected = currentValues[i] || '';

            // Гости, выбранные в других полях этой комнаты
            let selectedInOthers = currentValues.filter((fio, idx) => fio && idx !== i);

            // Список опций: все доступные - кто не выбран в других полях, плюс этот выбранный если не в available
            let options = available.filter(fio => !selectedInOthers.includes(fio));
            // Если уже выбранный гость не в списке available (например, уже был размещён, но теперь освобождён),
            // добавим его явно
            if (selected && !options.includes(selected)) {
                options.push(selected);
            }

            // "Пусто" всегда сверху
            let selectHtml = `<select class="form-select mb-2 guest-field" data-idx="${i}">
                                <option value="">Пусто</option>
                                ${options.map(fio =>`<option value="${fio}"${fio === selected ? ' selected' : ''}>${fio}</option>`).join('')}
                              </select>`;
            modalFields.insertAdjacentHTML('beforeend', selectHtml);
        }

        // События — при смене, перерисовываем все селекты
        modalFields.querySelectorAll('.guest-field').forEach(sel => {
            sel.addEventListener('change', function () {
                // Обновляем currentValues по индексу
                const idx = Number(sel.dataset.idx);
                currentValues[idx] = sel.value;
                drawModalFields();
            });
        });
    }

    // Сохранение
    modalForm.addEventListener('submit', function (e) {
        e.preventDefault();
        const guestFios = Array.from(modalFields.querySelectorAll('.guest-field')).map(f => f.value.trim());

        // Проверка на дубли
        const hasDuplicates = guestFios.some((fio, idx) => fio && guestFios.indexOf(fio) !== idx);
        if (hasDuplicates) {
            alert('Один и тот же гость не может быть выбран дважды в одну комнату!');
            return;
        }

        fetch('/placements/save/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.csrfToken,
            },
            body: JSON.stringify({
                room_id: editingRoomId,
                guest_fios: guestFios,
                arrival_id: document.querySelector('select[name="arrival"]').value
            })
        }).then(resp => resp.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    alert('Ошибка сохранения!');
                }
            });
    });
});
