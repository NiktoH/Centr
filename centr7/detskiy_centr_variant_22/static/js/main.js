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

document.addEventListener("DOMContentLoaded", () => {
  const groupsContainer = document.querySelector("[data-groups-list]");
  if (groupsContainer) {
    fetch("/api/groups/")
      .then((res) => res.json())
      .then((data) => {
        if (!data.groups || data.groups.length === 0) {
          groupsContainer.textContent = "Свободных групп сейчас нет.";
          return;
        }
        groupsContainer.innerHTML = data.groups
          .map(
            (g) =>
              `<div class="group-row"><strong>${g.title}</strong> (${g.club}) · ${g.age_range} · Свободно мест: ${g.free_places}</div>`
          )
          .join("");
      })
      .catch(() => {
        groupsContainer.textContent = "Не удалось загрузить список групп.";
      });
  }

  const chartContainer = document.querySelector("[data-attendance-chart]");
  if (chartContainer) {
    fetch("/api/attendance/")
      .then((res) => res.json())
      .then((data) => {
        const total = data.present + data.missed + data.excused;
        if (total === 0) {
          chartContainer.textContent = "Пока нет отметок о посещаемости.";
          return;
        }
        chartContainer.innerHTML = `
          <div>Присутствовал: <strong>${data.present}</strong></div>
          <div>Пропуск без причины: <strong>${data.missed}</strong></div>
          <div>Пропуск по справке: <strong>${data.excused}</strong></div>
        `;
      })
      .catch(() => {
        chartContainer.textContent = "Ошибка загрузки статистики.";
      });
  }
});
