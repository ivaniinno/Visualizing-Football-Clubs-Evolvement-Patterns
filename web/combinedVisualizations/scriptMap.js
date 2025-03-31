(() => {
  const mapContainer = document.getElementById('map');
  const width = mapContainer.offsetWidth;
  const height = mapContainer.offsetHeight;
  const years = Array.from({ length: 10 }, (_, i) => 2015 + i);

  let statsData = {};
  let countryMapping = {};
  let clubInfo = {};
  let countryInfo = {};
  let countryMappingData;

  let selectedCountries = {}


  const svg = d3.select("#map").append("svg")
    .attr("width", width)
    .attr("height", height);

  const g = svg.append("g");


  const projection = d3.geoMercator()
    .scale(150)
    .translate([width / 2, height / 1.5]);

  const legendSvg = d3.select("#map-legend")
    .append("svg")
    .attr("width", 140)
    .attr("height", 260);

  const heatmapLegendG = legendSvg.append('g').attr('transform', `translate(-10,30)`);
  const gradient = legendSvg
    .append('defs')
    .append('linearGradient')
    .attr('id', 'gradient')
    .attr('x1', '0%')
    .attr('x2', '0%')
    .attr('y1', '100%')
    .attr('y2', '0%');
  for (let i = 0; i <= 1; i += 0.1) {
    gradient
      .append('stop')
      .attr('offset', `${i * 100}%`)
      .attr('stop-color', d3.interpolateReds(i));
  }

  const path = d3.geoPath().projection(projection);

  const zoom = d3.zoom()
    .scaleExtent([1, 8])
    .translateExtent([[0, 0], [width, height]])
    .on("zoom", (event) => {
      g.attr("transform", event.transform);
    });

  svg.call(zoom);

  let geoData, currentYear = 2015, autoplay = false;

  const loadData = async () => {
    geoData = await d3.json("/data/world.geojson");
    statsData = {
      average_team_cost: await d3.json("/data/average_team_cost.json"),
      full_players_cost: await d3.json("/data/full_players_costs.json"),
      legionnaires_total_amount: await d3.json("/data/legionnaires_total_amount.json"),
      national_team_players_total_amount: await d3.json("/data/national_teams_players_total_amount.json"),
      total_average_age: await d3.json("/data/total_average_age.json"),
    };
    countryMappingData = await d3.json("/data/country_names.json");
    countryMapping = countryMappingData.reduce((acc, entry) => {
      acc[entry.EnglishName] = entry.NationalTeamID;
      return acc;
    }, {});
    clubInfo = await d3.json("/data/club_info.json");
    countryInfo = await d3.json("/data/country_info.json");
    updateMap();
  };

  const valueFields = {
    average_team_cost: "TeamCost",
    full_players_cost: "TotalCountryCost",
    legionnaires_total_amount: "TotalLegionnairesAmount",
    national_team_players_total_amount: "NationalPlayersCount",
    total_average_age: "AverageAgeAmongClubs",
  };

  const getColorScale = (measure, year) => {
    const valueField = valueFields[measure];
    const values = statsData[measure]
      .map(entry => entry.Year === year ? entry[valueField] : null)
      .filter(value => value > 0);
    const maxValue = d3.max(values);
    const minValue = d3.min(values);
    return d3.scaleSequential(d3.interpolateReds).domain([minValue, maxValue]);
  };

  const updateCountryInfo = (countryName, measure, year) => {
    const nationalTeamID = countryMapping[countryName];
    const valueField = valueFields[measure];
    const countryStats = statsData[measure].find(entry => entry.NationalTeamID === nationalTeamID && entry.Year === year);


    const euroMark = "€";
    const isEuroMeasure = measure === "average_team_cost" || measure === "full_players_cost";
    const valueSuffix = isEuroMeasure ? ` thousands ${euroMark}` : "";


    const countryInfoElement = document.getElementById("map-country-info");
    countryInfoElement.innerHTML = `
      <h1>${countryName}</h1>
      <p><strong>Measure:</strong> ${document.getElementById("measure").options[document.getElementById("measure").selectedIndex].text}</p>
      <p><strong>Value:</strong> ${countryStats?.[valueField] || "No data"}${valueSuffix}</p>
      <table id="country-info-table" style="width: 100%; border-collapse: collapse; margin-top: 10px;">
        <!-- Таблица будет заполняться динамически -->
      </table>
      <button id="view-on-scatter" style="margin-top: 10px; padding: 5px 10px; background-color: #007bb8; color: white; border: none; border-radius: 4px; cursor: pointer;">
        View on Scatter
      </button>
    `;


    document.getElementById("view-on-scatter").addEventListener("click", () => {
      navigateToScatter(countryName);
    });


    const countryClubs = clubInfo.filter(club => club.NationalTeamID === nationalTeamID);

    updateCountryInfoTable(
      document.getElementById("measure").options[document.getElementById("measure").selectedIndex].text,
      year,
      countryClubs
    );
  };

  const navigateToScatter = (countryName) => {

    const countryInfoEntry = countryMappingData.find(entry => entry.EnglishName === countryName);
    const russianName = countryInfoEntry?.NationalTeamName;

    if (russianName) {

      const countrySelect = document.getElementById("country-select");
      const countryOption = Array.from(countrySelect.options).find(option => option.value === russianName);

      if (countryOption) {
        countrySelect.value = russianName;


        const event = new Event("change");
        countrySelect.dispatchEvent(event);


        document.getElementById("scatter-section").scrollIntoView({ behavior: "smooth" });
      } else {
        console.warn(`Country "${russianName}" not found in the scatter plot dropdown.`);
      }
    } else {
      console.warn(`Country "${countryName}" not found in the countryInfo dataset.`);
    }
  };

  const updateMap = () => {
    const measure = document.getElementById("measure").value;
    const valueField = valueFields[measure];
    const colorScale = getColorScale(measure, currentYear);


    document.getElementById("map-country-info").innerHTML = `
      <h2>Country Info</h2>
      <p>Select a country to see details</p>
    `;

    g.selectAll("path").remove();

    g.selectAll("path")
      .data(geoData.features)
      .enter()
      .append("path")
      .attr("d", path)
      .attr("class", "country")
      .attr("fill", d => {
        const countryName = d.properties.name;
        const nationalTeamID = countryMapping[countryName];
        const countryStats = statsData[measure].find(entry => entry.NationalTeamID === nationalTeamID && entry.Year === currentYear);
        return countryStats ? colorScale(countryStats[valueField]) : "#ccc";
      })
      .on("click", (event, d) => {
        handleCountryClick(event, d);
        const countryName = d.properties.name;
        updateCountryInfo(countryName, measure, currentYear);
      })
      .append("title")
      .text(d => {
        const countryName = d.properties.name;
        const nationalTeamID = countryMapping[countryName];
        const countryStats = statsData[measure].find(entry => entry.NationalTeamID === nationalTeamID && entry.Year === currentYear);
        return `${countryName}: ${countryStats?.[valueField] || "No data"}`;
      });

    document.getElementById("current-year").textContent = currentYear;
    drawHeatmapLegend(measure, currentYear);

  };

  function drawHeatmapLegend(measure, year) {
    const valueField = valueFields[measure];
    const values = statsData[measure].map(entry => entry.Year === year ? entry[valueField] : null)
      .filter(value => value > 0);
    const maxValue = d3.max(values);
    const minValue = d3.min(values);


    removeElementIfExists('gradient-rect');
    legendSvg.append('rect')
      .attr('id', 'gradient-rect')
      .attr('x', 40)
      .attr('y', 0)
      .attr('width', 30)
      .attr('height', 200)
      .style('fill', 'url(#gradient)')
      .attr('transform', 'translate(0, 50)');


    const yAxisScale = d3.scaleLinear()
      .domain([minValue, maxValue])
      .range([200, 0]);

    drawVerticalAxis(yAxisScale, measure);
  }

  function removeElementIfExists(id) {
    const existing = legendSvg.select(`#${id}`);
    if (!existing.empty()) {
      existing.remove();
    }
  }

  function drawVerticalAxis(yAxisScale, measure) {
    if (!yAxisScale || typeof yAxisScale.domain !== "function") {
      console.error("Invalid axis scale!");
      return;
    }

    const yAxis = d3.axisRight(yAxisScale).ticks(5);


    removeElementIfExists('legend-axis');
    removeElementIfExists('legend-axis-title');


    legendSvg.append('g')
      .attr('id', 'legend-axis')
      .attr('transform', 'translate(75, 50)')
      .call(yAxis);

    legendSvg.append('text')
      .attr('id', 'legend-axis-title')
      .attr('transform', 'rotate(-90)')
      .attr('y', 13)
      .attr('x', -130)
      .attr('dy', '1em')
      .style('text-anchor', 'middle')
      .text(document.getElementById("measure").options[document.getElementById("measure").selectedIndex].text);
  }

  const getCountryNodes = () => g.selectAll('path').data(geoData.features)

  const getCountryNode = (countryName) => getCountryNodes()
    .filter((c) => countryName === c.properties.name)

  const highlightCountry = (countryName) => {
    getCountryNode(countryName)
      .classed('selectedCountry', true)
  }

  const unhighlightCountry = (countryName) => {
    getCountryNode(countryName)
      .classed('selectedCountry', false)
  }

  const highlightSelectedCountries = () => {
    getCountryNodes()
      .filter((c) => selectedCountries[c.properties.name])
      .classed('selectedCountry', true)
  }

  const handleCountryClick = (event, d) => {
    const ctrlPressed = event.ctrlKey
    const countryName = d.properties.name
    if (!ctrlPressed) {

      for (const key in selectedCountries) {
        if (key != countryName) {
          unhighlightCountry(key);
          delete selectedCountries[key]
        }
      }
    }

    if (selectedCountries[countryName]) {

      unhighlightCountry(countryName)
      delete selectedCountries[countryName]
    } else {
      highlightCountry(countryName)
      selectedCountries[countryName] = d
    }
    zoomToSelectedCountries()
  }

  const zoomToSelectedCountries = () => {
    const selectedCountriesGeoJSON = geoData.features.filter((c) => selectedCountries[c.properties.name])
    var minX = Number.POSITIVE_INFINITY;
    var minY = Number.POSITIVE_INFINITY;
    var maxX = Number.NEGATIVE_INFINITY;
    var maxY = Number.NEGATIVE_INFINITY;
    selectedCountriesGeoJSON.forEach((geojson) => {
      const bounds = path.bounds(geojson);
      minX = Math.min(minX, bounds[0][0]);
      minY = Math.min(minY, bounds[0][1]);
      maxX = Math.max(maxX, bounds[1][0]);
      maxY = Math.max(maxY, bounds[1][1]);
    })

    const dx = maxX - minX;
    const dy = maxY - minY;
    const x = (minX + maxX) / 2;
    const y = (minY + maxY) / 2;
    const newScale = Math.max(1, Math.min(4, 0.9 / Math.max(dx / width, dy / height)));

    const transform = d3.zoomIdentity
      .translate(width / 2, height / 2)
      .scale(newScale)
      .translate(-x, -y)

    g.transition().duration(750).call(zoom.transform, transform);
  }



  const changeYear = (direction) => {
    const index = years.indexOf(currentYear);
    currentYear = years[(index + direction + years.length) % years.length];
    updateMap();


    const selectedCountry = Object.keys(selectedCountries)[0];
    if (selectedCountry) {
      const measure = document.getElementById("measure").value;
      updateCountryInfo(selectedCountry, measure, currentYear);
    }
  };

  const toggleAutoplay = () => {
    autoplay = !autoplay;
    const playToggleButton = document.getElementById("play-toggle");
    playToggleButton.textContent = autoplay ? "⏸" : "▶";
    if (autoplay) {
      const interval = setInterval(() => {
        if (!autoplay) {
          clearInterval(interval);
        } else {
          changeYear(1);
        }
      }, 3000);
    }
  };

  document.getElementById("prev-year").addEventListener("click", () => changeYear(-1));
  document.getElementById("next-year").addEventListener("click", () => changeYear(1));
  document.getElementById("play-toggle").addEventListener("click", toggleAutoplay);
  document.getElementById("measure").addEventListener("change", updateMap);

  document.getElementById("zoom-in").addEventListener("click", () => {
    svg.transition().call(zoom.scaleBy, 1.5);
  });

  document.getElementById("zoom-out").addEventListener("click", () => {
    svg.transition().call(zoom.scaleBy, 0.75);
  });

  document.getElementById("reset").addEventListener("click", () => {
    svg.transition().call(zoom.transform, d3.zoomIdentity);
  });

  loadData();


  function updateCountryInfoTable(selectedMeasure, selectedYear, countryClubs) {
    const dataFiles = {
      "Average Team Cost": "data/total_team_cost.json",
      "Full Players Cost": "data/total_team_cost.json",
      "Legionnaires Total Amount": "data/legionnaires_per_team.json",
      "National Team Players Total Amount": "data/clubs_and_national_players.json",
      "Total Average Age": "data/average_age_per_team.json"
    };

    const measureKeys = {
      "Average Team Cost": "TeamCost",
      "Full Players Cost": "TeamCost",
      "Legionnaires Total Amount": "Legioners",
      "National Team Players Total Amount": "PlayersInNationalTeam",
      "Total Average Age": "AverageAge"
    };

    const measureKeysP = {
      "Average Team Cost": "Team Cost",
      "Full Players Cost": "Team Cost",
      "Legionnaires Total Amount": "Number of Legionnaires",
      "National Team Players Total Amount": "Number of Players in National Team",
      "Total Average Age": "Average Age"
    };

    const dataFile = dataFiles[selectedMeasure];
    const measureKey = measureKeys[selectedMeasure];

    d3.json(dataFile).then(data => {
      const table = d3.select("#country-info-table");
      table.html("");


      const headerRow = table.append("tr");
      headerRow.append("th").text("Club Name");
      headerRow.append("th").text(measureKeysP[selectedMeasure]);


      countryClubs.forEach(club => {
        const clubData = data.find(entry => entry.TeamID === club.TeamID && entry.Year === selectedYear);
        const value = clubData ? clubData[measureKey] : "N/A";

        const row = table.append("tr");
        row.append("td").text(club.Team_name);
        row.append("td").text(value);
      });
    }).catch(error => {
      console.error("Error loading data file:", error);
    });
  }
})();

