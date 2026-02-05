const API_ROOT = "https://polyhouse-qqiy.onrender.com/sensors";

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

    if (!res.ok) {
      throw new Error(`HTTP error ${res.status}`);
    }

    const text = await res.text();

    // 🔒 SAFE JSON PARSE (HTML error avoid)
    let json;
    try {
      json = JSON.parse(text);
    } catch (e) {
      console.error("Non JSON response:", text);
      alert("Server returned invalid data");
      return;
    }

    allData = json;
    renderTable();
  } catch (err) {
    console.error("Error fetching data:", err);
    alert("Unable to load sensor data");
  }
}

function exportToCSV() {
  if (!allData.length) {
    alert("No data available to export!");
    return;
  }

  const headers = ["S.No", "Temperature (°C)", "Timestamp"];
  const rows = allData.map((d, i) => [
    i + 1,
    d.waterTemperature ?? "-",
    d.timestamp ?? "-"
  ]);

  const csvContent = [headers, ...rows].map(r => r.join(",")).join("\n");

  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `polyhouse_data_${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

function renderTable() {
  size = parseInt(pageSizeSelect.value);
  const search = searchBox.value.trim().toLowerCase();

  let filtered = allData.filter(
    d =>
      d.waterTemperature?.toString().includes(search) ||
      d.timestamp?.toLowerCase().includes(search)
  );

  const totalPages = Math.ceil(filtered.length / size);
  page = Math.max(1, Math.min(page, totalPages));

  const start = (page - 1) * size;
  const pageData = filtered.slice(start, start + size);

  tbody.innerHTML = pageData.map(
    (d, i) => `
      <tr>
        <td>${start + i + 1}</td>
        <td>${d.waterTemperature ?? "-"}</td>
        <td>${d.timestamp ?? "-"}</td>
      </tr>
    `
  ).join("");

  pageInfo.textContent = `Page ${page} of ${totalPages || 1}`;
  prevBtn.disabled = page <= 1;
  nextBtn.disabled = page >= totalPages;
}

pageSizeSelect.onchange = () => { page = 1; renderTable(); };
searchBox.oninput = () => { page = 1; renderTable(); };
prevBtn.onclick = () => { if (page > 1) { page--; renderTable(); } };
nextBtn.onclick = () => { page++; renderTable(); };

viewDataBtn.onclick = () => window.location.href = "viewdata.html";
document.getElementById("exportBtn")?.addEventListener("click", exportToCSV);

loadData();