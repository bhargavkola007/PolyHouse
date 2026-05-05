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

// ✅ LOAD PAGINATED DATA (IMPORTANT FIX)
async function loadData() {
  try {
    size = parseInt(pageSizeSelect.value);

    const res = await fetch(`${API_ROOT}/data?page=${page}&size=${size}`);

    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`);
    }

    currentData = await res.json();
    renderTable();

  } catch (err) {
    console.error("Error fetching data:", err);
    alert("Server error. Please try again.");
  }
}

// ✅ RENDER TABLE (ONLY CURRENT PAGE DATA)
function renderTable() {
  const search = searchBox.value.trim().toLowerCase();

  let filtered = currentData.filter(d =>
    d.waterTemperature?.toString().toLowerCase().includes(search) ||
    d.timestamp?.toLowerCase().includes(search)
  );

  tbody.innerHTML = filtered.map((d, i) => `
    <tr>
      <td>${(page - 1) * size + i + 1}</td>
      <td>${d.waterTemperature ?? '-'}</td>
      <td>${d.timestamp ?? '-'}</td>
    </tr>
  `).join('');

  pageInfo.textContent = `Page ${page}`;
  prevBtn.disabled = page <= 1;
  nextBtn.disabled = currentData.length < size; // no more pages if less data
}

// ✅ PAGINATION BUTTONS
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

// ✅ PAGE SIZE CHANGE
pageSizeSelect.addEventListener("change", () => {
  page = 1;
  loadData();
});

// ✅ SEARCH (only current page)
searchBox.addEventListener("input", renderTable);

// ✅ EXPORT ONLY CURRENT PAGE (SAFE)
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
  link.click();
}

// ===== PROFILE MENU & LOGOUT =====
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

// ✅ NAVIGATION
viewDataBtn.onclick = () => window.location.href = 'viewdata.html';
document.getElementById("exportBtn").addEventListener("click", exportToCSV);

// 🚀 INITIAL LOAD
loadData();