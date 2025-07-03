// ЭТОТ JS ОТНОСИТСЯ К TEMPLATES/USER/APPLICATION_FORM & APPLICATION_EDIT
const userData = window.userData || {};
const relatives = window.relatives || [];
const initialGuests = window.initialGuests || [];
let guestIdx = initialGuests.length || 0;
const userQuota = window.free_quota || 0;

// Чтобы корректно работать при редактировании заявки:
function countPreferentialGuests() {
    const rows = document.querySelectorAll("#guests-list .guest-row");
    let count = 0;
    rows.forEach(row => {
        const qt = row.querySelector('.quota-type-select').value;
        if (qt === "Льготная квота") count += 1;
    });
    return count;
}

function updatePreferentialQuotaAvailable() {
    const span = document.getElementById('preferential-quota-available');
    if (span) {
        const quotaLeft = Math.max(userQuota - countPreferentialGuests(), 0);
        span.textContent = quotaLeft;
    }
}

// Если нужно убрать полностью quota-counter (по плану) — просто не используем updateQuotaDisplay
function updateQuotaDisplay() {}

function addGuestRow(source) {
    let data = {};
    let relationDisplay = '';
    if (typeof source === 'object') {
        data = source;
        relationDisplay = data.relationship || '';
    } else if (source.startsWith('user_')) {
        data = userData;
        relationDisplay = 'Сотрудник';
    } else if (source.startsWith('relative_')) {
        const relId = parseInt(source.split('_')[1]);
        data = relatives.find(r => r.id === relId) || {};
        relationDisplay = data.relationship || '';
    } else {
        data = {};
        relationDisplay = 'Не родственник';
    }
    const isManual = source === 'manual';
    const idx = guestIdx++;
    const guestsList = document.getElementById("guests-list");
    const birthdateValue =
        isManual ? '1998-03-04'
        : (data.birthdate && data.birthdate !== 'None' ? data.birthdate : '1998-03-04');
    const row = document.createElement('div');
    row.className = "guest-row row align-items-end mb-2";
    row.innerHTML = `
        <div class="col-md-2 mb-2 mb-md-0">
            <input type="text" class="form-control last-name-input" name="guests[${idx}][last_name]" placeholder="Фамилия" value="${isManual ? '' : (data.last_name || '')}">
        </div>
        <div class="col-md-2 mb-2 mb-md-0">
            <input type="text" class="form-control first-name-input" name="guests[${idx}][first_name]" placeholder="Имя" value="${isManual ? '' : (data.first_name || '')}">
        </div>
        <div class="col-md-2 mb-2 mb-md-0">
            <input type="text" class="form-control patronymic-input" name="guests[${idx}][patronymic]" placeholder="Отчество" value="${isManual ? '' : (data.patronymic || '')}">
        </div>
        <div class="col-md-2 mb-2 mb-md-0">
            <input type="date" class="form-control dob-input" name="guests[${idx}][birthdate]" value="${birthdateValue}">
        </div>
        <div class="col-md-2 mb-2 mb-md-0">
            <input type="text" class="form-control relationship-input" name="guests[${idx}][relationship]" value="${relationDisplay}" readonly>
        </div>
        <div class="col-md-2 mb-2 mb-md-0">
            <select class="form-select quota-type-select" name="guests[${idx}][quota_type]"></select>
        </div>
        <div class="col-md-1">
            <button type="button" class="btn btn-danger remove-guest-btn">✕</button>
        </div>
    `;
    guestsList.appendChild(row);

    // --- quota_type (select) ---
    let quotaTypes = [];
    if (isManual) {
        quotaTypes = window.QUOTA_TYPES ? window.QUOTA_TYPES.manual : ["Льготная квота", "Квота с полной стоимостью"];
    } else {
        quotaTypes = window.QUOTA_TYPES ? window.QUOTA_TYPES.user : ["Льготная квота", "50% квота", "Квота с полной стоимостью"];
    }
    const quotaSelect = row.querySelector('.quota-type-select');
    let selectedQuota = data.quota_type || quotaTypes[0]; // Если уже был выбран — подставим
    quotaTypes.forEach(function(qt) {
        const opt = document.createElement('option');
        opt.value = qt;
        opt.textContent = qt;
        if (qt === selectedQuota) opt.selected = true;
        quotaSelect.appendChild(opt);
    });

    // обновить число квот сразу
    updatePreferentialQuotaAvailable();

    row.querySelector('.remove-guest-btn').addEventListener('click', function() {
        row.remove();
        updatePreferentialQuotaAvailable();
    });

        // обновлять доступное кол-во льготников при изменении типа квоты
    quotaSelect.addEventListener('change', updatePreferentialQuotaAvailable);
}

document.addEventListener("DOMContentLoaded", function () {
    // показываем подсказку по квотам (если надо)
    updatePreferentialQuotaAvailable();

    // Если есть initialGuests (редактирование заявки) — восстанавливаем их
    if (Array.isArray(initialGuests) && initialGuests.length > 0) {
        initialGuests.forEach(addGuestRow);
    }
    const addBtn = document.getElementById("add-guest-btn");
    if (addBtn) {
        addBtn.addEventListener('click', function () {
            const select = document.getElementById('guest-type-select');
            addGuestRow(select.value);
        });
    }

    // Собираем гостей при отправке
    document.querySelector("form").addEventListener("submit", function(e) {
        const rows = document.querySelectorAll("#guests-list .guest-row");
        const guests = [];
        rows.forEach(row => {
            guests.push({
                last_name: row.querySelector('.last-name-input').value,
                first_name: row.querySelector('.first-name-input').value,
                patronymic: row.querySelector('.patronymic-input').value,
                birthdate: row.querySelector('.dob-input').value,
                relationship: row.querySelector('.relationship-input').value,
                quota_type: row.querySelector('.quota-type-select').value
            });
        });
        document.getElementById("id_guests").value = JSON.stringify(guests);
    });
});
