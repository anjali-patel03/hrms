(function () {
  const NO_OF_DAYS_IN_WEEK = 7;
  const NO_OF_MILLIS = 1000;

  function getYyyyMmDd(date) {
    return date.toISOString().slice(0, 10);
  }

  function addDays(date, days) {
    date.setDate(date.getDate() + days);
  }

  function clone(d) {
    return new Date(d.getTime());
  }

  function getWeeksBetween(start, end) {
    const msPerWeek = 7 * 24 * 60 * 60 * 1000;
    return Math.ceil((end - start) / msPerWeek);
  }

  function getMonthName(index, short) {
    const months = short
      ? ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
      : [
          "January",
          "February",
          "March",
          "April",
          "May",
          "June",
          "July",
          "August",
          "September",
          "October",
          "November",
          "December",
        ];
    return months[index];
  }

  class Heatmap {
    constructor(container, options) {
      this.container = container;
      this.options = options;
      this.data = options.data;
      this.colors = options.heatmapColors || {
        1: "#38b000",
        "-1": "#e63946",
        0: "#adb5bd",
      };
      this.start = new Date(options.start || new Date().getFullYear() + "-01-01");
      this.draw();
    }

    draw() {
      const data = this.data;
      const tooltip = this.options.tooltip || (() => "");

      const heatmap = document.createElement("div");
      heatmap.style.display = "grid";
      heatmap.style.gridTemplateColumns = "repeat(53, 12px)";
      heatmap.style.gap = "2px";

      let current = clone(this.start);
      const end = new Date(current.getFullYear(), 11, 31);

      while (current <= end) {
        const day = current.getDay(); // 0 (Sun) - 6 (Sat)
        const week = getWeeksBetween(this.start, current);
        const dateStr = getYyyyMmDd(current);
        const val = data[dateStr] ?? 0;

        const cell = document.createElement("div");
        cell.style.width = "12px";
        cell.style.height = "12px";
        cell.style.backgroundColor = this.colors[val] || this.colors[0];
        cell.title = tooltip({ date: dateStr, count: val });

        heatmap.appendChild(cell);
        addDays(current, 1);
      }

      this.container.innerHTML = "";
      this.container.appendChild(heatmap);
    }
  }

  window.Heatmap = Heatmap;
})();
