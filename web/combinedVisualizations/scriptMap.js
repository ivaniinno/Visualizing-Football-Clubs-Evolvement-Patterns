(() => {
  // Get the map container dimensions
  const mapContainer = document.getElementById('map');
  const width = mapContainer.offsetWidth;
  const height = mapContainer.offsetHeight;

  // Define the range of years for the visualization
  const years = Array.from({ length: 10 }, (_, i) => 2015 + i);

  // Initialize data structures for storing various datasets
  let statsData = {}; // Stores statistical data for different measures
  let countryMapping = {}; // Maps country names to their NationalTeamID
  let clubInfo = {}; // Stores information about clubs
  let countryInfo = {}; // Stores information about countries
  let countryMappingData; // Raw country mapping data
  let clubNameMapping = {}; // Maps club names to their translated names
  let countryNameMapping = {}; // Maps country names to their translated names

  let selectedCountries = {}; // Tracks selected countries on the map

  // Create the main SVG element for the map
  const svg = d3.select("#map").append("svg")
    .attr("width", width)
    .attr("height", height);

  const g = svg.append("g"); // Group element for map paths

  // Define the map projection
  const projection = d3.geoMercator()
    .scale(150)
    .translate([width / 2, height / 1.5]);

  // Create the legend SVG for the heatmap
  const legendSvg = d3.select("#map-legend")
    .append("svg")
    .attr("width", 140)
    .attr("height", 260);

  const heatmapLegendG = legendSvg.append('g').attr('transform', `translate(-10,30)`);

  // Define the gradient for the heatmap legend
  const gradient = legendSvg
    .append('defs')
    .append('linearGradient')
    .attr('id', 'gradient')
    .attr('x1', '0%')
    .attr('x2', '0%')
    .attr('y1', '100%')
    .attr('y2', '0%');

  // Populate the gradient with color stops
  for (let i = 0; i <= 1; i += 0.1) {
    gradient
      .append('stop')
      .attr('offset', `${i * 100}%`)
      .attr('stop-color', d3.interpolateReds(i));
  }

  // Define the path generator for drawing map features
  const path = d3.geoPath().projection(projection);

  // Define zoom behavior for the map
  const zoom = d3.zoom()
    .scaleExtent([1, 8]) // Set zoom scale limits
    .translateExtent([[0, 0], [width, height]]) // Set translation limits
    .on("zoom", (event) => {
      g.attr("transform", event.transform); // Apply zoom transformations
    });

  svg.call(zoom); // Attach zoom behavior to the SVG

  // Variables for storing geoJSON data and current state
  let geoData, currentYear = 2015, autoplay = false;

  // Load all required data files asynchronously
  Promise.all([
    d3.json("data/world.geojson"), // GeoJSON data for the world map
    d3.json("api/average_team_cost"), // Average team cost data
    d3.json("api/full_players_costs"), // Full players cost data
    d3.json("api/legionnaires_total_amount"), // Legionnaires total amount data
    d3.json("api/national_teams_players_total_amount"), // National team players total amount data
    d3.json("api/total_average_age"), // Total average age data
    d3.json("data/country_names.json"), // Country names mapping
    d3.json("api/club_info"), // Club information
    d3.json("api/country_info"), // Country information
    d3.json("data/club_name_mapping.json"), // Club name mapping
    d3.json("data/country_name_mapping.json") // Country name mapping
  ]).then(([geoDataResponse,
    averageTeamCostResponse,
    fullPlayersCostResponse,
    legionnairesTotalAmountResponse,
    nationalTeamPlayersTotalAmountResponse,
    totalAverageAgeResponse,
    countryMappingDataResponse,
    clubInfoResponse,
    countryInfoResponse,
    clubNameMappingResponse,
    countryNameMappingResponse]) => {
    // Assign loaded data to variables
    geoData = geoDataResponse;
    statsData = {
      average_team_cost: averageTeamCostResponse,
      full_players_cost: fullPlayersCostResponse,
      legionnaires_total_amount: legionnairesTotalAmountResponse,
      national_team_players_total_amount: nationalTeamPlayersTotalAmountResponse,
      total_average_age: totalAverageAgeResponse,
    };
    countryMappingData = countryMappingDataResponse;

    // Process country mapping data
    countryMapping = countryMappingData.reduce((acc, entry) => {
      acc[entry.EnglishName] = entry.NationalTeamID;
      return acc;
    }, {});

    clubInfo = clubInfoResponse;
    countryInfo = countryInfoResponse;

    // Process club and country name mappings
    clubNameMapping = clubNameMappingResponse.reduce((acc, entry) => {
      acc[entry.TeamName] = entry.TranslatedName;
      return acc;
    }, {});

    countryNameMapping = countryNameMappingResponse.reduce((acc, entry) => {
      acc[entry.NationalTeamName] = entry.TranslatedName;
      return acc;
    }, {});

    // Initialize the map visualization
    updateMap();
  });

  // Mapping of measure keys to their corresponding data fields
  const valueFields = {
    average_team_cost: "TeamCost",
    full_players_cost: "TotalCountryCost",
    legionnaires_total_amount: "TotalLegionnairesAmount",
    national_team_players_total_amount: "NationalPlayersCount",
    total_average_age: "AverageAgeAmongClubs",
  };

  // Function to generate a color scale for a given measure and year
  const getColorScale = (measure, year) => {
    const valueField = valueFields[measure];
    const values = statsData[measure]
      .map(entry => entry.Year === year ? entry[valueField] : null)
      .filter(value => value > 0);
    const maxValue = d3.max(values);
    const minValue = d3.min(values);
    return d3.scaleSequential(d3.interpolateReds).domain([minValue, maxValue]);
  };

  // Function to update country information displayed on the map
  const updateCountryInfo = (countryName, measure, year) => {
    const nationalTeamID = countryMapping[countryName];
    const valueField = valueFields[measure];
    const countryStats = statsData[measure].find(entry => entry.NationalTeamID === nationalTeamID && entry.Year === year);

    // Determine value suffix based on the measure
    const euroMark = "€";
    const isEuroMeasure = measure === "average_team_cost" || measure === "full_players_cost";
    const valueSuffix = isEuroMeasure ? ` thousands ${euroMark}` : "";

    // Update the country info section
    const countryInfoElement = document.getElementById("map-country-info");
    countryInfoElement.innerHTML = `
      <h1>${countryName}</h1>
      <p><strong>Measure:</strong> ${document.getElementById("measure").options[document.getElementById("measure").selectedIndex].text}</p>
      <p><strong>Value:</strong> ${countryStats?.[valueField] || "No data"}${valueSuffix}</p>
      <table id="country-info-table" style="width: 100%; border-collapse: collapse; margin-top: 10px;">
        <!-- Table will be dynamically populated -->
      </table>
      <button id="view-on-scatter" style="margin-top: 10px; padding: 5px 10px; background-color: #f9eadb; color: #333; border: none; border-radius: 4px; cursor: pointer;">
        View on Scatter
      </button>
    `;

    // Add event listener for the "View on Scatter" button
    document.getElementById("view-on-scatter").addEventListener("click", () => {
      navigateToScatter(countryName);
    });

    // Get clubs associated with the selected country
    const countryClubs = clubInfo.filter(club => club.NationalTeamID === nationalTeamID);

    // Update the country info table with club data
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
      const englishName = countryNameMapping[russianName] || russianName; // Map to English name

      const countrySelect = document.getElementById("country-select");
      const countryOption = Array.from(countrySelect.options).find(option => option.value === englishName);

      if (countryOption) {
        countrySelect.value = englishName;

        const event = new Event("change");
        countrySelect.dispatchEvent(event);

        document.getElementById("scatter-section").scrollIntoView({ behavior: "smooth" });
      } else {
        console.warn(`Country "${englishName}" not found in the scatter plot dropdown.`);
      }
    } else {
      console.warn(`Country "${countryName}" not found in the countryInfo dataset.`);
    }
  };

  const updateMap = () => {
    const measure = document.getElementById("measure").value;
    const valueField = valueFields[measure];
    const colorScale = getColorScale(measure, currentYear);

    // Reset country info section
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

    // Remove existing gradient rectangle if it exists
    removeElementIfExists('gradient-rect');
    legendSvg.append('rect')
      .attr('id', 'gradient-rect')
      .attr('x', 40)
      .attr('y', 0)
      .attr('width', 30)
      .attr('height', 200)
      .style('fill', 'url(#gradient)')
      .attr('transform', 'translate(0, 50)');

    // Define the scale for the legend's vertical axis
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

    // Remove existing axis and title if they exist
    removeElementIfExists('legend-axis');
    removeElementIfExists('legend-axis-title');

    // Append the new axis
    legendSvg.append('g')
      .attr('id', 'legend-axis')
      .attr('transform', 'translate(75, 50)')
      .call(yAxis);

    // Append the axis title
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

  function getEnglishClubName(clubName) {
    return clubNameMapping[clubName] || clubName;
  }

  function updateCountryInfoTable(selectedMeasure, selectedYear, countryClubs) {
    const dataFiles = {
      "Average Team Cost": "api/total_team_cost",
      "Full Players Cost": "api/total_team_cost",
      "Legionnaires Total Amount": "api/legionnaires_per_team",
      "National Team Players Total Amount": "api/clubs_and_national_players",
      "Total Average Age": "api/average_age_per_team"
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

      // Append table headers
      const headerRow = table.append("tr");
      headerRow.append("th").text("Club Name");
      headerRow.append("th").text(measureKeysP[selectedMeasure]);

      // Append table rows with club data
      countryClubs.forEach(club => {
        const clubData = data.find(entry => entry.TeamID === club.TeamID && entry.Year === selectedYear);
        const value = clubData ? clubData[measureKey] : "N/A";
        if (!value){
          value = "N/A";
        }

        const row = table.append("tr");
        row.append("td").text(getEnglishClubName(club.TeamName)); // Use English name
        row.append("td").text(value);
      });
    }).catch(error => {
      console.error("Error loading data file:", error);
    });
  }
})();

