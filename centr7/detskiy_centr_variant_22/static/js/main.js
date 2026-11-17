document.addEventListener("DOMContentLoaded", () => {
    const chart = document.querySelector("#attendance-chart");
    if (chart) {
        fetch(chart.dataset.url)
            .then(response => response.json())
            .then(data => {
                chart.innerHTML = "";
                if (!data.values.length) {
                    chart.textContent = "Данных о посещениях пока нет.";
                    return;
                }
                const max = Math.max(...data.values, 1);
                data.labels.forEach((label, index) => {
                    const row = document.createElement("div");
                    row.className = "bar-row";
                    const title = document.createElement("span");
                    title.textContent = label;
                    const track = document.createElement("div");
                    track.className = "bar-track";
                    const fill = document.createElement("div");
                    fill.className = "bar-fill";
                    fill.style.width = `${data.values[index] / max * 100}%`;
                    track.append(fill);
                    const value = document.createElement("strong");
                    value.textContent = data.values[index];
                    row.append(title, track, value);
                    chart.append(row);
                });
            })
            .catch(() => chart.textContent = "Не удалось загрузить статистику.");
    }

    const groupList = document.querySelector("#group-live-list");
    if (groupList) {
        fetch(groupList.dataset.url)
            .then(response => response.json())
            .then(data => {
                groupList.innerHTML = "";
                data.groups.forEach(group => {
                    const row = document.createElement("div");
                    row.className = "group-live-row";
                    const title = document.createElement("strong");
                    title.textContent = group.title;
                    const details = document.createElement("span");
                    details.textContent = `${group.club} · ${group.age} лет · свободных мест: ${group.free_places}`;
                    row.append(title, details);
                    groupList.append(row);
                });
                if (!data.groups.length) groupList.textContent = "Нет доступных групп.";
            })
            .catch(() => groupList.textContent = "Не удалось загрузить список групп.");
    }
});
