const API_ROOT = "https://polyhouse-qqiy.onrender.com/sensors";

const tbody = document.querySelector("#dataTable tbody");
const prevBtn = document.getElementById("prevBtn");
const nextBtn = document.getElementById("nextBtn");
const pageInfo = document.getElementById("pageInfo");
const pageSizeSelect = document.getElementById("pageSize");
const searchBox = document.getElementById("searchBox");
const viewDataBtn = document.getElementById("viewDataBtn");
const exportBtn = document.getElementById("exportBtn");

let allData = [];
let page = 1;
let size = parseInt(pageSizeSelect.value);
let totalPages = 1;
let totalRecords = 0;

// ================= LOAD PAGINATED DATA =================
async function loadData() {
  try {
    size = parseInt(pageSizeSelect.value);

    const res = await fetch(`${API_ROOT}/data?page=${page}&size=${size}`);

    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`);
    }

    const result = await res.json();

    allData = result.data || [];
    totalRecords = result.total || 0;
    totalPages = result.totalPages || Math.ceil(totalRecords / size) || 1;

    renderTable();
  } catch (err) {
    console.error("Error fetching data:", err);
    alert("Unable to load sensor data");
  }
}

// ================= EXPORT CURRENT PAGE CSV =================
function exportToCSV() {
  if (!allData.length) {
    alert("No data available to export!");
    return;
  }

  const headers = ["S.No", "Temperature (°C)", "Timestamp"];

  const rows = allData.map((d, i) => [
    (page - 1) * size + i + 1,
    d.waterTemperature ?? "-",
    d.timestamp ?? "-"
  ]);

  const csvContent = [headers, ...rows]
    .map(row => row.join(","))
    .join("\n");

  const blob = new Blob([csvContent], {
    type: "text/csv;charset=utf-8;"
  });

  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.setAttribute("href", url);
  link.setAttribute(
    "download",
    `polyhouse_data_page_${page}_${new Date().toISOString().slice(0, 10)}.csv`
  );

  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// ================= PROFILE MENU & LOGOUT =================

const profileMenu = document.querySelector(".profile-menu");

if (typeof token !== "undefined" && !token && profileMenu) {
  profileMenu.remove();
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

// ================= RENDER TABLE =================
function renderTable() {
  const search = searchBox.value.trim().toLowerCase();

  let filtered = allData.filter(
    d =>
      d.waterTemperature?.toString().toLowerCase().includes(search) ||
      d.timestamp?.toLowerCase().includes(search)
  );

  tbody.innerHTML = filtered
    .map(
      (d, i) => `
      <tr>
        <td>${(page - 1) * size + i + 1}</td>
        <td>${d.waterTemperature ?? "-"}</td>
        <td>${d.timestamp ?? "-"}</td>
      </tr>
    `
    )
    .join("");

  pageInfo.textContent =
    `Page ${page} of ${totalPages} (${totalRecords} records)`;

  prevBtn.disabled = page <= 1;
  nextBtn.disabled = page >= totalPages;
}

// ================= EVENTS =================
pageSizeSelect.addEventListener("change", () => {
  page = 1;
  loadData();
});

searchBox.addEventListener("input", () => {
  renderTable();
});

prevBtn.addEventListener("click", () => {
  if (page > 1) {
    page--;
    loadData();
  }
});

nextBtn.addEventListener("click", () => {
  if (page < totalPages) {
    page++;
    loadData();
  }
});

if (viewDataBtn) {
  viewDataBtn.onclick = () => {
    window.location.href = "viewdata.html";
  };
}

if (exportBtn) {
  exportBtn.addEventListener("click", exportToCSV);
}

loadData();