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
