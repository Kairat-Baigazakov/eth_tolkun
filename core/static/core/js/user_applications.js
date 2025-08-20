// core/static/core/js/user_applications.js

document.addEventListener('DOMContentLoaded', function() {

    // ===== 1. Кнопка "Отправить заявку" (активация по времени подачи) =====
    document.querySelectorAll('tr[data-app-id]').forEach(function(row) {
        const status = row.dataset.appStatus;
        const startStr = row.dataset.appStart;
        const endStr = row.dataset.appEnd;
        const btn = row.querySelector('.send-app-btn');
        if (!btn) return;

        function updateButton() {
            const now = new Date();
            const start = new Date(startStr.replace(' ', 'T'));
            const end = new Date(endStr.replace(' ', 'T'));
            if (status === "new" && now >= start && now <= end) {
                btn.style.display = "";
                btn.disabled = false;
            } else {
                btn.style.display = "none";
            }
        }
        updateButton();
        setInterval(updateButton, 1000);
    });

    function normalizeQuotaLabel(raw) {
        if (!raw) return "Полная стоимость";
        raw = String(raw).trim();
        if (raw === "50% квота" || raw === "50% стоимость") return "50% стоимость";
        if (raw === "Квота с полной стоимостью" || raw === "Полная стоимость") return "Полная стоимость";
        // всё остальное считаем льготной
        return "Льготная квота";
    }

    function fmt(n) {
        // красивый вывод суммы
        return new Intl.NumberFormat('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(Number(n || 0));
    }

    document.querySelectorAll('.btn-pay').forEach(function (btn) {
        btn.addEventListener('click', function () {
            const appId = Number(btn.dataset.appId);

            const appEntry = (window.APPLICATIONS_GUESTS || []).find(x => Number(x.id) === appId);
                // 1) из подготовленного массива
            let buildingType = appEntry && appEntry.building_type;
            // 2) резерв: из data-атрибута кнопки
            if (!buildingType) {
              buildingType = btn.dataset.buildingType || "";
            }

            if (!buildingType) {
                alert("Не определен корпус (тип здания) для заявки. Обратитесь к модератору.");
                return;
            }

            let totalPrice = 0;
            let totalNSP = 0;
            let totalNDS = 0;
            let totalNMA = 0;

            (appEntry.guests || []).forEach(g => {
                const quotaLabel = normalizeQuotaLabel(g.quota_type);
                const key = buildingType + "::" + quotaLabel;
                const rate = (window.RATES_MAP || {})[key];
                if (!rate) {
                console.warn("Нет тарифа для ключа", key);
                return;
                }
                totalPrice += parseFloat(rate.price || 0);
                totalNSP  += parseFloat(rate.nsp   || 0);
                totalNDS  += parseFloat(rate.nds   || 0);
                totalNMA  += parseFloat(rate.nma   || 0);
            });

            const html = `
                <div class="mb-3">
                    <p>Заявка <b>№${appId}</b>. Корпус: <b>${buildingType}</b></p>
                    <p><b>Сумма к оплате (основная цена + НСП): ${fmt(totalPrice + totalNSP)} сом</b></p>
                    <p class="mb-1">Реквизиты (основная цена + НСП):</p>
                    <div class="small text-muted mb-3">
                        Счет: Национального банка<br>
                        <b>Средства от реализации путевок: 1013990100001075</b><br>
                        Назначение платежа: ФИО, № Заезда, Дата (период) заезда
                    </div>

                    <p><b>Сумма к оплате НДС: ${fmt(totalNDS)} сом</b></p>
                    <p class="mb-1">Реквизиты (НДС):</p>
                    <div class="small text-muted mb-3">
                        Счет: Национального банка<br>
                        <b>Налог на добавленную стоимость (НДС) - УОЦ Толкун: 1013920100002407</b>
                    </div>

                    <p><b>Сумма к оплате НМА: ${fmt(totalNMA)} сом</b></p>
                    <p class="mb-1">Реквизиты (НМА):</p>
                    <div class="small text-muted">
                        Счет: Национального банка<br>
                        <b>Подоходный налог на мат.выгоду (ссуда, путевки и др.): 1013920100000989</b><br>
                        <i>Примечание: Налог на материальную выгоду удерживается с заработной платы работников.
                        Данную сумму необходимо оплачивать пенсионерам и служащим, находящимся в декретных отпусках.
                        Налог на материальную выгоду по полной стоимости не взимается.</i>
                    </div>
                </div>
            `;

            document.getElementById('payment-info').innerHTML = html;

            const modal = new bootstrap.Modal(document.getElementById('paymentModal'));
            modal.show();
            document.getElementById('payment-form').dataset.appId = String(appId);
        });
    });

    // ===== 3. Отправка файлов оплаты =====
    document.getElementById('payment-form').addEventListener('submit', function(e) {
        e.preventDefault();
        const appId = this.dataset.appId;
        const filesInput = document.getElementById('payment-files');
        if (!filesInput.files.length) {
            alert('Пожалуйста, выберите хотя бы один файл для загрузки.');
            return;
        }

        const submitBtn = this.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.textContent = "Отправка...";

        const formData = new FormData();
        for (let file of filesInput.files) {
            formData.append('files', file);
        }

        // csrf
        formData.append('csrfmiddlewaretoken', getCSRFToken());

        fetch(`/applications/${appId}/payment_check/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(resp => resp.json())
        .then(data => {
            if (data.success) {
                alert('Документы отправлены. Ваша заявка ожидает проверки.');
                location.reload();
            } else {
                alert('Ошибка: ' + (data.error || 'Не удалось отправить документы.'));
            }
        })
        .catch(() => {
            alert('Ошибка сети или сервера. Попробуйте позже.');
        })
        .finally(() => {
            submitBtn.disabled = false;
            submitBtn.textContent = "Оплачено";
        });
    });

    // Функция получения csrf-токена
    function getCSRFToken() {
        const el = document.querySelector('[name=csrfmiddlewaretoken]');
        return el ? el.value : '';
    }

});
