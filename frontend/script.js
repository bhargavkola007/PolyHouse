const API_ROOT = "https://polyhouse-qqiy.onrender.com/sensors";

const tbody = document.querySelector("#dataTable tbody");
const prevBtn = document.getElementById("prevBtn");
const nextBtn = document.getElementById("nextBtn");
const pageInfo = document.getElementById("pageInfo");
const pageSizeSelect = document.getElementById("pageSize");
const searchBox = document.getElementById("searchBox");
const viewDataBtn = document.getElementById("viewDataBtn");

let page = 1;
let size = parseInt(pageSizeSelect.value);
let currentData = [];
let isLoading = false;

// ================= LOAD DATA =================
async function loadData() {
  if (isLoading) return; // prevent spam clicks
  isLoading = true;

  try {
    size = parseInt(pageSizeSelect.value);

    // 🔄 Show loading
    tbody.innerHTML = `<tr><td colspan="3">Loading...</td></tr>`;

    const res = await fetch(`${API_ROOT}/data?page=${page}&size=${size}`);

    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`);
    }

    const data = await res.json();

    // ❗ If no data and page > 1 → go back
    if (data.length === 0 && page > 1) {
      page--;
      isLoading = false;
      return loadData();
    }

    currentData = data;
    renderTable();

  } catch (err) {
    console.error("Error fetching data:", err);
    tbody.innerHTML = `<tr><td colspan="3">⚠ Server error</td></tr>`;
  }

  isLoading = false;
}

// ================= RENDER =================
function renderTable() {
  const search = searchBox.value.trim().toLowerCase();

  let filtered = currentData.filter(d =>
    d.waterTemperature?.toString().toLowerCase().includes(search) ||
    d.timestamp?.toLowerCase().includes(search)
  );

  if (!filtered.length) {
    tbody.innerHTML = `<tr><td colspan="3">No data found</td></tr>`;
  } else {
    tbody.innerHTML = filtered.map((d, i) => `
      <tr>
        <td>${(page - 1) * size + i + 1}</td>
        <td>${d.waterTemperature ?? '-'}</td>
        <td>${d.timestamp ?? '-'}</td>
      </tr>
    `).join('');
  }

  pageInfo.textContent = `Page ${page}`;
  prevBtn.disabled = page <= 1;
  nextBtn.disabled = currentData.length < size;
}

// ================= PAGINATION =================
prevBtn.addEventListener("click", () => {
  if (page > 1) {
    page--;
    loadData();
  }
});

nextBtn.addEventListener("click", () => {
  page++;
  loadData();
});

// ================= PAGE SIZE =================
pageSizeSelect.addEventListener("change", () => {
  page = 1;
  loadData();
});

// ================= SEARCH (DEBOUNCE) =================
let searchTimeout;

searchBox.addEventListener("input", () => {
  clearTimeout(searchTimeout);

  searchTimeout = setTimeout(() => {
    renderTable();
  }, 300);
});

// ================= EXPORT =================
function exportToCSV() {
  if (!currentData.length) {
    alert("No data available to export!");
    return;
  }

  const headers = ["S.No", "Temperature (°C)", "Timestamp"];

  const rows = currentData.map((d, i) => [
    (page - 1) * size + i + 1,
    d.waterTemperature ?? "-",
    d.timestamp ?? "-"
  ]);

  const csvContent = [headers, ...rows]
    .map(row => row.join(","))
    .join("\n");

  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);

  const link = document.createElement("a");
  link.href = url;
  link.download = `polyhouse_page_${page}.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// ================= PROFILE =================
const profileMenu = document.querySelector(".profile-menu");

if (typeof token === "undefined" || !token) {
  if (profileMenu) profileMenu.remove();
}

const profileIcon = document.getElementById("profileIcon");
const dropdown = document.getElementById("profileDropdown");
const logoutBtn = document.getElementById("logoutBtn");

if (profileIcon && dropdown && logoutBtn) {
  profileIcon.addEventListener("click", (e) => {
    e.stopPropagation();
    dropdown.classList.toggle("active");
  });

  logoutBtn.addEventListener("click", () => {
    localStorage.removeItem("token");
    window.location.href = "login.html";
  });

  document.addEventListener("click", (e) => {
    if (!e.target.closest(".profile-menu")) {
      dropdown.classList.remove("active");
    }
  });
}

// ================= NAVIGATION =================
if (viewDataBtn) {
  viewDataBtn.onclick = () => window.location.href = 'viewdata.html';
}

const exportBtn = document.getElementById("exportBtn");
if (exportBtn) {
  exportBtn.addEventListener("click", exportToCSV);
}

// ================= INIT =================
loadData();