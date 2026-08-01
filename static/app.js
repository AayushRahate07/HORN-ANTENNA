let currentData = null;
let selectedSourceFiles = [];

document.addEventListener("DOMContentLoaded", () => {
  // File inputs display name update
  // Ground + Sky: single files
  ["ground", "sky"].forEach((type) => {
    const input = document.getElementById(`file-${type}`);
    const nameSpan = document.getElementById(`name-${type}`);

    input.addEventListener("change", (e) => {
      if (e.target.files.length > 0) {
        nameSpan.textContent = e.target.files[0].name;
        nameSpan.style.color = "#00f2fe";
      } else {
        nameSpan.textContent = "Choose file...";
        nameSpan.style.color = "#8a99ad";
      }
    });
  });

  // ============================================================
  // SOURCE FILE MANAGER
  // ============================================================

  const sourceInput = document.getElementById("file-source");

  const sourceName = document.getElementById("name-source");

  const sourceBox = document.getElementById("source-box");

  const sourcePopup = document.getElementById("source-popup");

  const sourceList = document.getElementById("source-list");

  const sourceCount = document.getElementById("source-count");

  const addSourceBtn = document.getElementById("btn-add-source");

  // ------------------------------------------------------------
  // Add newly selected files
  // ------------------------------------------------------------

  sourceInput.addEventListener("change", (e) => {
    const newFiles = Array.from(e.target.files);

    newFiles.forEach((file) => {
      // Prevent duplicate filename + size combinations
      const alreadyExists = selectedSourceFiles.some(
        (source) =>
          source.file.name === file.name && source.file.size === file.size,
      );

      if (!alreadyExists) {
        selectedSourceFiles.push({
          file: file,
          enabled: true,
        });
      }
    });

    // Reset native input so the same file can
    // potentially be selected again later.
    sourceInput.value = "";

    renderSourceManager();

    // Keep popup open after selection
    sourcePopup.classList.add("open");
  });

  // ------------------------------------------------------------
  // Open file picker when clicking ADD MORE
  // ------------------------------------------------------------

  addSourceBtn.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();

    if (sourceInput.showPicker) {
      sourceInput.showPicker();
    } else {
      sourceInput.click();
    }
  });

  // ------------------------------------------------------------
  // Clicking source box pins/unpins popup
  // ------------------------------------------------------------

  sourceBox.addEventListener("click", (e) => {
    // Allow normal file picker if no sources exist yet
    if (selectedSourceFiles.length === 0) {
      return;
    }

    e.preventDefault();

    sourcePopup.addEventListener("click", (e) => {
      e.stopPropagation();
    });
  });

  // ------------------------------------------------------------
  // Clicking popup shouldn't close it
  // ------------------------------------------------------------

  sourcePopup.addEventListener("click", (e) => {
    e.stopPropagation();
  });

  // ------------------------------------------------------------
  // Clicking anywhere outside closes pinned popup
  // ------------------------------------------------------------

  document.addEventListener("click", (e) => {
    if (!sourcePopup.contains(e.target) && !sourceBox.contains(e.target)) {
      sourcePopup.classList.remove("open");
    }
  });

  // ------------------------------------------------------------
  // Render popup contents
  // ------------------------------------------------------------

  function renderSourceManager() {
    sourceList.innerHTML = "";

    // Number of selected files
    sourceCount.textContent = selectedSourceFiles.length;

    // Main source-box text
    if (selectedSourceFiles.length === 0) {
      sourceName.textContent = "Choose files...";
      sourceName.style.color = "#8a99ad";
    } else if (selectedSourceFiles.length === 1) {
      sourceName.textContent = selectedSourceFiles[0].file.name;

      sourceName.style.color = "#00f2fe";
    } else {
      const enabledCount = selectedSourceFiles.filter(
        (source) => source.enabled,
      ).length;

      sourceName.textContent = `${enabledCount}/${selectedSourceFiles.length} scans active`;

      sourceName.style.color = "#00f2fe";
    }

    // Create each row
    selectedSourceFiles.forEach((source, index) => {
      const row = document.createElement("div");

      row.className = "source-item" + (source.enabled ? "" : " disabled");

      // Filename
      const name = document.createElement("span");

      name.className = "source-item-name";

      name.textContent = source.file.name;

      name.title = source.file.name;

      // Checkbox
      const checkbox = document.createElement("input");

      checkbox.type = "checkbox";

      checkbox.className = "source-checkbox";

      checkbox.checked = source.enabled;

      checkbox.addEventListener("change", () => {
        selectedSourceFiles[index].enabled = checkbox.checked;

        renderSourceManager();

        sourcePopup.classList.add("open");
      });

      // Delete
      const deleteBtn = document.createElement("button");

      deleteBtn.type = "button";

      deleteBtn.className = "source-delete";

      deleteBtn.innerHTML = "×";

      deleteBtn.title = "Remove source";

      deleteBtn.addEventListener("click", () => {
        selectedSourceFiles.splice(index, 1);

        renderSourceManager();

        sourcePopup.classList.add("open");
      });

      row.appendChild(name);
      row.appendChild(checkbox);
      row.appendChild(deleteBtn);

      sourceList.appendChild(row);
    });
  }

  // Tab switching
  const tabBtns = document.querySelectorAll(".tab-btn");
  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      tabBtns.forEach((b) => b.classList.remove("active"));
      document
        .querySelectorAll(".tab-pane")
        .forEach((p) => p.classList.remove("active"));

      btn.classList.add("active");
      const targetTab = document.getElementById(btn.dataset.tab);
      targetTab.classList.add("active");

      if (currentData) {
        renderCharts(currentData);
      }
    });
  });

  // Form submission
  const form = document.getElementById("observation-form");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const btnProcess = document.getElementById("btn-process");
    btnProcess.disabled = true;
    btnProcess.innerHTML = "<span>...</span>";

    const formData = new FormData();
    formData.append(
      "ground_file",
      document.getElementById("file-ground").files[0],
    );
    formData.append("sky_file", document.getElementById("file-sky").files[0]);
    const activeSources = selectedSourceFiles.filter(
      (source) => source.enabled,
    );

    if (activeSources.length === 0) {
      alert("Select at least one active source scan.");

      btnProcess.disabled = false;

      btnProcess.innerHTML = "<span>PROCESS OBSERVATION</span>";

      return;
    }

    activeSources.forEach((source) => {
      formData.append("source_files", source.file);
    });
    formData.append("sky_temp_k", document.getElementById("sky-temp").value);
    formData.append(
      "ground_temp_k",
      document.getElementById("ground-temp").value,
    );
    formData.append("observatory_lat", document.getElementById("lat").value);
    formData.append("observatory_lon", document.getElementById("lon").value);
    formData.append("observatory_alt", document.getElementById("alt").value);
    formData.append(
      "source_coords_str",
      document.getElementById("coords").value,
    );

    try {
      const response = await fetch("/api/process", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const err = await response.json();
        alert(`Error: ${err.detail || "Processing failed"}`);
        return;
      }

      currentData = await response.json();
      document.getElementById("empty-state").classList.add("hidden");
      document.getElementById("export-section").classList.remove("hidden");

      renderCharts(currentData);
    } catch (error) {
      console.error("API Error:", error);
      alert(`Network error: ${error.message}`);
    } finally {
      btnProcess.disabled = false;
      btnProcess.innerHTML = "<span>PROCESS OBSERVATION</span>";
    }
  });

  // Export CSV
  // Export CSV
  document.getElementById("btn-export-csv").addEventListener("click", () => {
    if (!currentData || !currentData.observations) return;

    currentData.observations.forEach((obs) => {
      let csvContent = "data:text/csv;charset=utf-8,";

      csvContent +=
        "Frequency_MHz,Ground_Watts,Sky_Watts,Source_Watts,Tr_Original_K,Tr_Corrected_K,Ts_K,Brightness_Temp_K,Velocity_km_s,Velocity_Corrected_km_s\n";

      for (let i = 0; i < obs.channels; i++) {
        const row = [
          obs.freq_mhz[i],
          obs.power_ground_watts[i],
          obs.power_sky_watts[i],
          obs.power_source_watts[i],
          obs.tr_original_k[i],
          obs.tr_corrected_k[i],
          obs.ts_k[i],
          obs.brightness_temp_k[i],
          obs.velocity_raw_kms[i],
          obs.velocity_corrected_kms[i],
        ].join(",");

        csvContent += row + "\n";
      }

      const encodedUri = encodeURI(csvContent);
      const link = document.createElement("a");

      link.setAttribute("href", encodedUri);

      const originalName = obs.name.replace(/\.csv$/i, "");

      link.setAttribute("download", `${originalName}_calibrated.csv`);

      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    });
  });
});

function renderCharts(data) {
  const observations = data.observations;

  if (!observations || observations.length === 0) {
    console.error("No observations returned from API.");
    return;
  }

  // Shared calibration data
  // Ground/Sky are identical for every observation.
  const reference = observations[0];

  const plotlyLayoutDefaults = {
    paper_bgcolor: "transparent",
    plot_bgcolor: "rgba(0,0,0,0.2)",

    font: {
      color: "#f0f4f8",
      family: "Fira Sans, sans-serif",
    },

    margin: {
      t: 65,
      r: 30,
      l: 70,
      b: 70,
    },

    xaxis: {
      gridcolor: "rgba(255,255,255,0.08)",
      zerolinecolor: "rgba(255,255,255,0.2)",
      automargin: true,
    },

    yaxis: {
      gridcolor: "rgba(255,255,255,0.08)",
      zerolinecolor: "rgba(255,255,255,0.2)",
      automargin: true,
    },

    hoverlabel: {
      font: {
        family: "Fira Sans, sans-serif",
        size: 12,
      },
    },
  };

  // ============================================================
  // 1. VLSR VELOCITY SPECTRUM
  // One brightness-temperature trace per source observation
  // ============================================================

  const vlsrTraces = observations.map((obs) => ({
    x: obs.velocity_corrected_kms,
    y: obs.brightness_temp_k,

    type: "scatter",
    mode: "lines",

    name: obs.name,

    line: {
      width: 2,
    },

    hovertemplate:
      `<b>${obs.name}</b><br>` +
      "Velocity: %{x:.2f} km/s<br>" +
      "Tb: %{y:.2f} K" +
      "<extra></extra>",
  }));

  const layoutVlsr = {
    ...plotlyLayoutDefaults,

    margin: {
      t: 82,
      r: 20,
      l: 70,
      b: 75,
    },

    title: {
      text: "Calibrated Brightness Temperature vs VLSR Corrected Radial Velocity",

      x: 0.5,
      xanchor: "center",

      y: 0.98,
      yanchor: "top",

      font: {
        family: "Fira Sans, sans-serif",
        size: 17,
      },
    },

    legend: {
      orientation: "h",

      x: 0.5,
      xanchor: "center",

      y: 1.015,
      yanchor: "bottom",

      bgcolor: "rgba(0,0,0,0)",

      font: {
        family: "Fira Sans, sans-serif",
        size: 12,
      },
    },

    xaxis: {
      ...plotlyLayoutDefaults.xaxis,
      title: "Radial Velocity (km/s)",
    },

    yaxis: {
      ...plotlyLayoutDefaults.yaxis,
      title: "Brightness Temperature (K)",
    },
  };

  Plotly.newPlot("plot-vlsr", vlsrTraces, layoutVlsr, {
    responsive: true,
    displayModeBar: true,
    displaylogo: false,
  });

  // ============================================================
  // 2. TEMPERATURE CALIBRATION
  //
  // Receiver temperature is calibration-derived and therefore
  // plotted once.
  //
  // Ts and Tb vary by source, so each source gets its own traces.
  // ============================================================

  const temperatureTraces = [];

  // Shared receiver temperature
  temperatureTraces.push({
    x: reference.freq_mhz,
    y: reference.tr_corrected_k,

    type: "scatter",
    mode: "lines",

    name: "Receiver Temp Tr",

    line: {
      color: "#4facfe",
      width: 1.5,
      dash: "dot",
    },

    hovertemplate:
      "<b>Receiver Temp Tr</b><br>" +
      "Frequency: %{x:.4f} MHz<br>" +
      "Tr: %{y:.2f} K" +
      "<extra></extra>",
  });

  // Source-dependent temperatures
  observations.forEach((obs) => {
    temperatureTraces.push({
      x: obs.freq_mhz,
      y: obs.ts_k,

      type: "scatter",
      mode: "lines",

      name: `${obs.name} · Ts`,

      line: {
        width: 1.2,
        dash: "dot",
      },

      opacity: 0.65,

      hovertemplate:
        `<b>${obs.name}</b><br>` +
        "Frequency: %{x:.4f} MHz<br>" +
        "Ts: %{y:.2f} K" +
        "<extra></extra>",
    });

    temperatureTraces.push({
      x: obs.freq_mhz,
      y: obs.brightness_temp_k,

      type: "scatter",
      mode: "lines",

      name: `${obs.name} · Tb`,

      line: {
        width: 2,
      },

      hovertemplate:
        `<b>${obs.name}</b><br>` +
        "Frequency: %{x:.4f} MHz<br>" +
        "Tb: %{y:.2f} K" +
        "<extra></extra>",
    });
  });

  const layoutTemp = {
    ...plotlyLayoutDefaults,

    margin: {
      t: 80,
      r: 20,
      l: 70,
      b: 75,
    },

    title: {
      text: "Calibrated Temperatures across Frequency Spectrum",

      x: 0.5,
      xanchor: "center",

      y: 0.985,
      yanchor: "top",

      font: {
        family: "Fira Sans, sans-serif",
        size: 17,
      },
    },

    legend: {
      orientation: "h",

      xref: "paper",
      yref: "paper",

      x: 0.5,
      xanchor: "center",

      y: 1.02,
      yanchor: "bottom",

      bgcolor: "rgba(0,0,0,0)",

      font: {
        family: "Fira Sans, sans-serif",
        size: 12,
      },
    },

    xaxis: {
      ...plotlyLayoutDefaults.xaxis,
      title: "Frequency (MHz)",
    },

    yaxis: {
      ...plotlyLayoutDefaults.yaxis,
      title: "Temperature (K)",
    },
  };

  Plotly.newPlot("plot-temp", temperatureTraces, layoutTemp, {
    responsive: true,
    displayModeBar: true,
    displaylogo: false,
  });

  // ============================================================
  // 3. POWER SPECTRA
  //
  // Ground + Sky plotted ONCE.
  // Every source gets its own Source Power trace.
  // ============================================================

  const powerTraces = [];

  // Ground calibration
  powerTraces.push({
    x: reference.freq_mhz,
    y: reference.power_ground_watts,

    type: "scatter",
    mode: "lines",

    name: "Ground Power",

    line: {
      color: "#a96600",
      width: 1.5,
    },

    hovertemplate:
      "<b>Ground</b><br>" +
      "Frequency: %{x:.4f} MHz<br>" +
      "Power: %{y:.4e} W" +
      "<extra></extra>",
  });

  // Sky calibration
  powerTraces.push({
    x: reference.freq_mhz,
    y: reference.power_sky_watts,

    type: "scatter",
    mode: "lines",

    name: "Sky Power",

    line: {
      color: "#0075e2",
      width: 1.5,
    },

    hovertemplate:
      "<b>Sky</b><br>" +
      "Frequency: %{x:.4f} MHz<br>" +
      "Power: %{y:.4e} W" +
      "<extra></extra>",
  });

  // One source-power trace for every observation
  observations.forEach((obs) => {
    powerTraces.push({
      x: obs.freq_mhz,
      y: obs.power_source_watts,

      type: "scatter",
      mode: "lines",

      name: obs.name,

      line: {
        width: 1.7,
      },

      hovertemplate:
        `<b>${obs.name}</b><br>` +
        "Frequency: %{x:.4f} MHz<br>" +
        "Power: %{y:.4e} W" +
        "<extra></extra>",
    });
  });

  const layoutPower = {
    ...plotlyLayoutDefaults,

    margin: {
      t: 82,
      r: 20,
      l: 70,
      b: 75,
    },

    title: {
      text: "Raw Transformed Power Scans (Watts)",

      x: 0.5,
      xanchor: "center",

      y: 0.98,
      yanchor: "top",

      font: {
        family: "Fira Sans, sans-serif",
        size: 17,
      },
    },

    legend: {
      orientation: "h",

      x: 0.5,
      xanchor: "center",

      y: 1.015,
      yanchor: "bottom",

      bgcolor: "rgba(0,0,0,0)",

      font: {
        family: "Fira Sans, sans-serif",
        size: 12,
      },
    },

    xaxis: {
      ...plotlyLayoutDefaults.xaxis,
      title: "Frequency (MHz)",
    },

    yaxis: {
      ...plotlyLayoutDefaults.yaxis,
      title: "Power (Watts)",
    },
  };

  Plotly.newPlot("plot-power", powerTraces, layoutPower, {
    responsive: true,
    displayModeBar: true,
    displaylogo: false,
  });
}
