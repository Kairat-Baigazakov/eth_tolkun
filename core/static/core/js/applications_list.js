// applications_list.js

document.addEventListener('DOMContentLoaded', function() {
    // Обработка действий (approve/reject/revision)
    let revisionAppId = null;

    document.querySelectorAll('.app-action-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            const appId = btn.dataset.appId;
            const action = btn.dataset.action;

            if (action === "revision") {
                // Открыть модальное окно для комментария
                revisionAppId = appId;
                const commentField = document.getElementById('revisionComment');
                commentField.value = '';
                const modal = new bootstrap.Modal(document.getElementById('revisionModal'));
                modal.show();
                // Установим обработчик для кнопки "Ок"
                document.getElementById('sendRevisionBtn').onclick = function() {
                    const comment = commentField.value;
                    sendAction(appId, action, comment, modal);
                    location.reload();
                };
            } else {
                // approve или reject — сразу отправляем
                sendAction(appId, action);
                location.reload();
            }
        });
    });

    document.querySelectorAll('.btn-pay').forEach(function (btn) {
        btn.addEventListener('click', function () {
            if (!confirm('Перевести заявку в статус "Ожидает оплаты"?')) return;

            const appId = btn.dataset.appId;
            fetch(`/applications/${appId}/action/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': window.CSRF_TOKEN,
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: new URLSearchParams({action: 'mark_payment_pending'})
            })
            .then(resp => resp.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    alert(data.error || "Ошибка!");
                }
            });
        });
    });

    // Обработка кнопки "Оплачено"
    document.querySelectorAll('.btn-approve-payment').forEach(function (btn) {
        btn.addEventListener('click', function () {
            const appId = btn.getAttribute('data-app-id');
            if (!confirm("Подтвердить, что оплата прошла?")) return;
            fetch('/applications/' + appId + '/approve_payment/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': window.CSRF_TOKEN,
                },
            })
            .then(resp => resp.json())
            .then(data => {
                if (data.success) location.reload();
                else alert('Ошибка!');
            });
        });
    });

    function sendAction(appId, action, comment = '', modal=null) {
        fetch(`/applications/${appId}/action/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': window.CSRF_TOKEN || document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `action=${action}&comment=${encodeURIComponent(comment)}`
        })
        .then(resp => resp.json())
        .then(data => {
            if (data.success) {
                // Обновить статус прямо в таблице
                const row = document.querySelector(`[data-app-id="${appId}"]`).closest('tr');
                const statusTd = row.querySelector('td.status-cell');
                if (statusTd) {
                    statusTd.innerHTML = statusBadge(data.status_code, data.status);
                }
                row.querySelectorAll('.app-action-btn').forEach(b => b.style.display = 'none');
                if (modal) modal.hide();
                // обновить комментарий, если передан
                if (action === "revision") {
                    const commentCell = row.querySelector('td:last-child');
                    if (commentCell) commentCell.textContent = comment || '-';
                }
            }
        });
    }

    // Строим красивую "badge" для статусов
    function statusBadge(status_code, status_text) {
        let cls = "bg-light text-dark";
        if (status_code === "approved") cls = "bg-success";
        else if (status_code === "revision") cls = "bg-warning text-dark";
        else if (status_code === "rejected") cls = "bg-danger";
        else if (status_code === "sent") cls = "bg-info text-dark";
        else if (status_code === "new") cls = "bg-secondary";
        else if (status_code === "cancelled") cls = "bg-warning text-dark";
        return `<span class="badge ${cls}">${status_text}</span>`;
    }

    // Фильтрация по нескольким статусам
    const checkboxes = document.querySelectorAll('.status-checkbox');
    const hidden = document.getElementById('status-hidden');
    const form = checkboxes.length > 0 ? checkboxes[0].closest('form') : null;

    function updateHiddenAndSubmit() {
        const selected = [];
        checkboxes.forEach(cb => { if (cb.checked) selected.push(cb.value); });
        hidden.value = selected.join(',');
        if (form) form.submit();
    }
    checkboxes.forEach(cb => {
        cb.addEventListener('change', updateHiddenAndSubmit);
    });
});
