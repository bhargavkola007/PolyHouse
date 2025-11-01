const API_ROOT = "http://localhost:8080/sensors";
const tbody = document.querySelector("#dataTable tbody");
const prevBtn = document.getElementById("prevBtn");
const nextBtn = document.getElementById("nextBtn");
const pageInfo = document.getElementById("pageInfo");
const pageSizeSelect = document.getElementById("pageSize");
const searchBox = document.getElementById("searchBox");
const viewDataBtn = document.getElementById("viewDataBtn");

let allData = [];
let page = 1;
let size = parseInt(pageSizeSelect.value);

async function loadData() {
  try {
    const res = await fetch(`${API_ROOT}/data`);
    allData = await res.json();
    renderTable();
  } catch (err) {
    console.error("Error fetching data:", err);
  }
}

function renderTable() {
  size = parseInt(pageSizeSelect.value);
  const search = searchBox.value.trim().toLowerCase();

  let filtered = allData.filter(
    d =>
      d.waterTemperature?.toString().toLowerCase().includes(search) ||
      d.timestamp?.toLowerCase().includes(search)
  );

  const totalPages = Math.ceil(filtered.length / size);
  page = Math.max(1, Math.min(page, totalPages));

  const start = (page - 1) * size;
  const pageData = filtered.slice(start, start + size);

  tbody.innerHTML = pageData
    .map(
      (d, i) => `
      <tr>
        <td>${start + i + 1}</td>
        <td>${d.waterTemperature ?? '-'}</td>
        <td>${d.timestamp ?? '-'}</td>
      </tr>
    `
    )
    .join('');

  pageInfo.textContent = `Page ${page} of ${totalPages || 1} (${filtered.length} records)`;
  prevBtn.disabled = page <= 1;
  nextBtn.disabled = page >= totalPages;
}

pageSizeSelect.addEventListener("change", () => {
  page = 1;
  renderTable();
});

searchBox.addEventListener("input", () => {
  page = 1;
  renderTable();
});

prevBtn.addEventListener("click", () => {
  if (page > 1) {
    page--;
    renderTable();
  }
});

nextBtn.addEventListener("click", () => {
  page++;
  renderTable();
});

viewDataBtn.onclick = () => window.location.href = 'viewdata.html';

loadData();
