document.addEventListener('DOMContentLoaded', function () {
    const modal = new bootstrap.Modal(document.getElementById('placementModal'));
    const modalForm = document.getElementById('modal-form');
    const modalFields = document.getElementById('modal-fields');
    const assignBtn = document.getElementById('assignRoomsBtn');

    let editingRoomId = null;
    let roomCapacity = 0;
    let currentValues = [];
    let allGuests = window.allGuests || [];

    if (assignBtn) {
        assignBtn.addEventListener('click', function() {
            if (!confirm('Подтвердите заселение гостей по комнатам?')) return;

            fetch(window.assignRoomsUrl, {
                method: "POST",
                headers: {
                    "X-CSRFToken": window.csrfToken,
                },
            })
            .then(resp => resp.json())
            .then(data => {
                if (data.success) {
                    alert('Гости успешно заселены!');
                    location.reload();
                } else {
                    alert('Ошибка: ' + (data.error || 'Не удалось заселить гостей'));
                }
            });
        });
    }

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
        // Destroy Select2 на старых полях
        $(modalFields).find('.guest-select').select2('destroy');

        modalFields.innerHTML = '';

        let guests = window.availableGuests.map(g => ({ fio: g.fio, app_id: g.application_id }));

        for (let i = 0; i < roomCapacity; i++) {
            let selected = currentValues[i] || '';
            let selectedInOthers = currentValues.filter((fio, idx) => fio && idx !== i);
            let options = guests.filter(g => !selectedInOthers.includes(g.fio) || g.fio === selected);

            let selectedGuest = allGuests.find(g => g.fio === selected);
            if (selected && !options.some(g => g.fio === selected)) {
                options.push({
                    fio: selected,
                    app_id: selectedGuest ? selectedGuest.app_id : "?"
                });
            }

            let selectHtml = `
                <div class="input-group mb-2" style="align-items: center;">
                    <select class="form-select guest-field guest-select" data-idx="${i}">
                        <option value="">🟦 Пусто (свободно)</option>
                        ${options.map(g =>
                            `<option value="${g.fio}"${g.fio === selected ? ' selected' : ''}>👤 ${g.fio} (№${g.app_id || g.application_id || "?"})</option>`
                          ).join('')}
                    </select>
                    <button type="button" class="btn btn-outline-secondary clear-field-btn" data-idx="${i}" tabindex="-1" title="Очистить">&times;</button>
                </div>
            `;
            modalFields.insertAdjacentHTML('beforeend', selectHtml);
        }

        // init Select2
        $(modalFields).find('.guest-select').select2({
            width: '100%',
            dropdownParent: $('#placementModal'),
            placeholder: 'Выберите гостя',
            allowClear: false,
            templateResult: function(data) {
                if (!data.id) return $('<span style="color:#0d6efd;">🟦 Пусто (свободно)</span>');
                const text = data.text || '';
                let [_, fio, app] = text.match(/👤 ([^\(]+) \(№([^)]+)\)/) || [null, text, ''];
                return $(`<div><b>${fio.trim()}</b> ${app ? '<small class="text-muted">№'+app+'</small>' : ''}</div>`);
            },
            templateSelection: function(data) {
                if (!data.id) return $('<span style="color:#0d6efd;">🟦 Пусто</span>');
                let text = data.text || '';
                let [_, fio, app] = text.match(/👤 ([^\(]+) \(№([^)]+)\)/) || [null, text, ''];
                return $(`<span>👤 ${fio.trim()} ${app ? '<small class="text-muted">(№'+app+')</small>' : ''}</span>`);
            }
        });

        // Повесить события на очистку после каждой перерисовки
        modalFields.querySelectorAll('.clear-field-btn').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                const idx = Number(btn.dataset.idx);
                currentValues[idx] = '';
                drawModalFields();
            });
        });

        // Перерисовка при смене select2
        modalFields.querySelectorAll('.guest-field').forEach(sel => {
            sel.addEventListener('change', function () {
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
