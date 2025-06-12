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
        relationDisplay = data.relation || ''; // <--- используем relation, не relationship!
    } else {
        data = {};
        relationDisplay = 'Не родственник';
    }

    const isManual = source === 'manual';
    const idx = guestIdx++;
    const guestsList = document.getElementById("guests-list");

    const row = document.createElement('div');
    row.className = "guest-row row align-items-end mb-2";
    row.innerHTML = `
        <div class="col-md-2 mb-2 mb-md-0">
            <input type="text" class="form-control" name="guests[${idx}][last_name]" placeholder="Фамилия" value="${isManual ? '' : (data.last_name || '')}">
        </div>
        <div class="col-md-2 mb-2 mb-md-0">
            <input type="text" class="form-control" name="guests[${idx}][first_name]" placeholder="Имя" value="${isManual ? '' : (data.first_name || '')}">
        </div>
        <div class="col-md-2 mb-2 mb-md-0">
            <input type="text" class="form-control" name="guests[${idx}][patronymic]" placeholder="Отчество" value="${isManual ? '' : (data.patronymic || '')}">
        </div>
        <div class="col-md-2 mb-2 mb-md-0">
            <input type="date" class="form-control" name="guests[${idx}][date_of_birth]" value="${isManual ? '1998-03-04' : (data.date_of_birth || '1998-03-04')}">
        </div>
        <div class="col-md-2 mb-2 mb-md-0">
            <input type="text" class="form-control" name="guests[${idx}][relationship]" value="${relationDisplay}" readonly>
        </div>
        <div class="col-md-2">
            <button type="button" class="btn btn-danger remove-guest-btn">✕</button>
        </div>
    `;
    guestsList.appendChild(row);

    // При добавлении уменьшаем квоту и обновляем счетчик
    currentQuota--;
    updateQuotaDisplay();

    // Удалить строку — возвращаем квоту обратно
    row.querySelector('.remove-guest-btn').addEventListener('click', function() {
        row.remove();
        currentQuota++;
        updateQuotaDisplay();
    });
}

document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("add-guest-btn").addEventListener('click', function () {
        const select = document.getElementById('guest-type-select');
        addGuestRow(select.value);
    });
    updateQuotaDisplay(); // Первичная инициализация
});
