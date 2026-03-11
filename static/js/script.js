function toggleSidebar() {
  const sidebar = document.getElementById("sidebar");
  const overlay = document.querySelector(".overlay");
  sidebar.classList.toggle("active");
  overlay.classList.toggle("active");
}

if (window.innerWidth <= 768) {
  document.querySelectorAll(".sidebar-nav a").forEach((link) => {
    link.addEventListener("click", () => {
      toggleSidebar();
    });
  });
}

const selector = document.getElementById("matchday-select");
const matchdays = document.querySelectorAll(".matchday-section");

selector.addEventListener("change", function () {
  const selectedIndex = this.value;

  matchdays.forEach((matchday) => {
    matchday.style.display = "none";
  });

  const selectedMatchday = document.querySelector(
    `[data-matchday="${selectedIndex}"]`,
  );
  if (selectedMatchday) {
    selectedMatchday.style.display = "block";
  }
});

function showConference(conferenceIndex) {
  const tables = document.querySelectorAll(".conference-table");
  tables.forEach((table) => {
    table.style.display = "none";
  });

  const buttons = document.querySelectorAll(".tab-button");
  buttons.forEach((button) => {
    button.classList.remove("active");
  });

  const selectedTable = document.querySelector(
    `[data-conference="${conferenceIndex}"]`,
  );
  if (selectedTable) {
    selectedTable.style.display = "block";
  }

  buttons[conferenceIndex].classList.add("active");
}

document.addEventListener('DOMContentLoaded', function() {
    const firstConference = document.querySelector('.conference-table[data-conference="0"]');
    if (firstConference) {
        showConference(0);
    }
});

function showStat(statType) {
    const tables = document.querySelectorAll('.stats-table');
    tables.forEach(table => {
        table.style.display = 'none';
    });

    const buttons = document.querySelectorAll('.stats-tabs .tab-button');
    buttons.forEach(button => {
        button.classList.remove('active');
    });

    const selectedTable = document.querySelector(`[data-stat="${statType}"]`);
    if (selectedTable) {
        selectedTable.style.display = 'block';
    }

    const clickedButton = event.target;
    clickedButton.classList.add('active');
}