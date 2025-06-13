const userData = window.userData || {};
const relatives = window.relatives || [];
let guestIdx = 0;
let currentQuota = window.userQuota || 0;

function updateQuotaDisplay() {
    const counter = document.getElementById("quota-counter");
    const addBtn = document.getElementById("add-guest-btn");
    counter.textContent = currentQuota;
    if (currentQuota <= 0) {
        addBtn.classList.remove('btn-success');
        addBtn.classList.add('btn-secondary');
        addBtn.disabled = true;
    } else {
        addBtn.classList.add('btn-success');
        addBtn.classList.remove('btn-secondary');
        addBtn.disabled = false;
    }
}

function addGuestRow(source) {
    if (currentQuota <= 0) return;
    let data = {};
    let relationDisplay = '';

    if (source.startsWith('user_')) {
        data = userData;
        relationDisplay = 'Сотрудник';
    } else if (source.startsWith('relative_')) {
        const relId = parseInt(source.split('_')[1]);
        data = relatives.find(r => r.id === relId) || {};
        relationDisplay = data.relationship  || '';
    } else {
        data = {};
        relationDisplay = 'Не родственник';
    }

    const isManual = source === 'manual';
    const idx = guestIdx++;
    const guestsList = document.getElementById("guests-list");

    const birthdateValue = isManual ? '1998-03-04' : (data.birthdate && data.birthdate !== 'None' ? data.birthdate : '1998-03-04');

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
        <div class="col-md-2">
            <button type="button" class="btn btn-danger remove-guest-btn">✕</button>
        </div>
    `;
    guestsList.appendChild(row);

    // Удалить строку
    row.querySelector('.remove-guest-btn').addEventListener('click', function() {
        row.remove();
        currentQuota += 1;
        updateQuotaDisplay();
    });

    currentQuota -= 1;
    updateQuotaDisplay();
}

document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("add-guest-btn").addEventListener('click', function () {
        const select = document.getElementById('guest-type-select');
        addGuestRow(select.value);
    });
    updateQuotaDisplay();
});

document.querySelector("form").addEventListener("submit", function(e) {
    const rows = document.querySelectorAll("#guests-list .guest-row");
    const guests = [];
    rows.forEach(row => {
        guests.push({
            last_name: row.querySelector('.last-name-input').value,
            first_name: row.querySelector('.first-name-input').value,
            patronymic: row.querySelector('.patronymic-input').value,
            birthdate: row.querySelector('.dob-input').value,
            relationship: row.querySelector('.relationship-input').value
        });
    });
    document.getElementById("id_guests").value = JSON.stringify(guests);
});