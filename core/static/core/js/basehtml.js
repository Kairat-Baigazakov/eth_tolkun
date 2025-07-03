function updateTime() {
    const now = new Date();
    const time = now.toLocaleTimeString('ru-RU', {
        hour: '2-digit', minute: '2-digit', second: '2-digit'
    });
    document.getElementById('current-time').textContent = time;
}

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('current-date').textContent =
        new Date().toLocaleDateString('ru-RU');
    updateTime();
    setInterval(updateTime, 1000);
})

document.getElementById('current-year').textContent = new Date().getFullYear();

document.addEventListener("DOMContentLoaded", function(){
    flatpickr("input[type='date']", {
        dateFormat: "Y-m-d"
    });
    flatpickr("input[type='datetime-local']", {
        enableTime: true,
        dateFormat: "Y-m-d\\TH:i"
    });
});