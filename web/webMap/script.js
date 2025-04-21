const mapContainer = document.getElementById('map');
const width = mapContainer.offsetWidth;
const height = mapContainer.offsetHeight;
const years = Array.from({ length: 11 }, (_, i) => 2014 + i);

const countryMapping = {
  "Эстония": "Estonia",
  "Англия": "England",
  "Черногория": "Montenegro",
  "Румыния": "Romania",
  "Финляндия": "Finland",
  "Казахстан": "Kazakhstan",
  "Норвегия": "Norway",
  "Италия": "Italy",
  "Мальта": null,
  "Армения": "Armenia",
  "Исландия": "Iceland",
  "Франция": "France",
  "Швеция": "Sweden",
  "Испания": "Spain",
  "Фарерские острова": null,
  "Кипр": "Cyprus",
  "Сан-Марино": null,
  "Азербайджан": "Azerbaijan",
  "Дания": "Denmark",
  "Израиль": "Israel",
  "Украина": "Ukraine",
  "Беларусь": "Belarus",
  "Уэльс": null,
  "Португалия": "Portugal",
  "Северная Македония": null,
  "Россия": "Russia",
  "Андорра": null,
  "Нидерланды": "Netherlands",
  "Греция": "Greece",
  "Бельгия": "Belgium",
  "Босния и Герцеговина": "Bosnia and Herzegovina",
  "Венгрия": "Hungary",
  "Хорватия": "Croatia",
  "Турция": "Turkey",
  "Грузия": "Georgia",
  "Ирландия": "Ireland",
  "Молдова": "Moldova",
  "Люксембург": "Luxembourg",
  "Австрия": "Austria",
  "Шотландия": null,
  "Албания": "Albania",
  "Северная Ирландия": null,
  "Чехия": "Czech Republic",
  "Словакия": "Slovakia",
  "Германия": "Germany",
  "Сербия": null,
  "Болгария": "Bulgaria",
  "Монако": null,
  "Лихтенштейн": null,
  "Польша": "Poland",
  "Косово": "Kosovo",
  "Швейцария": "Switzerland",
  "Словения": "Slovenia",
  "Латвия": "Latvia",
  "Литва": "Lithuania",
  "Гибралтар": null
};


const reversedCountryMapping = {
  "Estonia": "Эстония",
  "England": "Англия",
  "Montenegro": "Черногория",
  "Romania": "Румыния",
  "Finland": "Финляндия",
  "Kazakhstan": "Казахстан",
  "Norway": "Норвегия",
  "Italy": "Италия",
  "Armenia": "Армения",
  "Iceland": "Исландия",
  "France": "Франция",
  "Sweden": "Швеция",
  "Spain": "Испания",
  "Cyprus": "Кипр",
  "Azerbaijan": "Азербайджан",
  "Denmark": "Дания",
  "Israel": "Израиль",
  "Ukraine": "Украина",
  "Belarus": "Беларусь",
  "Portugal": "Португалия",
  "Russia": "Россия",
  "Netherlands": "Нидерланды",
  "Greece": "Греция",
  "Belgium": "Бельгия",
  "Bosnia and Herzegovina": "Босния и Герцеговина",
  "Hungary": "Венгрия",
  "Croatia": "Хорватия",
  "Turkey": "Турция",
  "Georgia": "Грузия",
  "Ireland": "Ирландия",
  "Moldova": "Молдова",
  "Luxembourg": "Люксембург",
  "Austria": "Австрия",
  "Albania": "Албания",
  "Czech Republic": "Чехия",
  "Slovakia": "Словакия",
  "Germany": "Германия",
  "Bulgaria": "Болгария",
  "Poland": "Польша",
  "Kosovo": "Косово",
  "Switzerland": "Швейцария",
  "Slovenia": "Словения",
  "Latvia": "Латвия",
  "Lithuania": "Литва"
};

let selectedCountries = {}


const svg = d3.select("#map").append("svg")
  .attr("width", width)
  .attr("height", height);

const g = svg.append("g");


const projection = d3.geoMercator()
  .scale(150)
  .translate([width / 2, height / 1.5]);

const legendSvg = d3.select("#legend")
  .append("svg")
  .attr("width", 140)
  .attr("height", 260);

const heatmapLegendG = legendSvg.append('g').attr('transform', `translate(-10,30)`);
// Define gradient
const gradient = legendSvg
  .append('defs')
  .append('linearGradient')
  .attr('id', 'gradient')
  .attr('x1', '0%')
  .attr('x2', '0%')
  .attr('y1', '100%')
  .attr('y2', '0%');
// Define stops for the gradient based on the color scale
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

let geoData, statsData, currentYear = 2014, autoplay = false;

const loadData = async () => {
  geoData = await d3.json("/data/world.geojson");
  statsData = await d3.json("/data/country_year_stats.json");
  // geoData.features = geoData.features.filter(feature => {
  //     const countryName = feature.properties.name;
  //     return reversedCountryMapping.hasOwnProperty(countryName);
  // });
  updateMap();
};

const getColorScale = (measure, year) => {
  const values = Object.keys(statsData).map(country => {
    const englishName = countryMapping[country];
    return englishName ? statsData[country]?.[String(year)]?.[measure] || 0 : 0;
  });
  const maxValue = d3.max(values);
  const minValue = d3.min(values);
  return d3.scaleSequential(d3.interpolateReds).domain([0, maxValue]);
};

const updateMap = () => {
  const measure = document.getElementById("measure").value;
  const colorScale = getColorScale(measure, currentYear);

  g.selectAll("path").remove();

  g.selectAll("path")
    .data(geoData.features)
    .enter()
    .append("path")
    .attr("d", path)
    .attr("class", "country")
    .attr("fill", d => {
      const countryName = d.properties.name;

      const countryStats = statsData[reversedCountryMapping[countryName]]?.[currentYear]?.[measure] || 0;
      return colorScale(countryStats);
    })
    .on("click", (event, d) => {
      handleCountryClick(event, d);
      const countryName = d.properties.name;
      const info = statsData[reversedCountryMapping[countryName]]?.[currentYear]?.[measure] || 0;

      // Обновляем информацию справа
      document.getElementById("country-info").innerHTML = info
        ? `<h3>${countryName}</h4><p>${document.getElementById("measure").options[document.getElementById("measure").selectedIndex].text}: ${statsData[reversedCountryMapping[d.properties.name]]?.[currentYear]?.[measure] || 0}</p>`
        : `<h3>${countryName}</h4><p>No data</p>`;
    })
    .append("title")
    .text(d => `${d.properties.name} (${document.getElementById("measure").options[document.getElementById("measure").selectedIndex].text}: ${statsData[reversedCountryMapping[d.properties.name]]?.[currentYear]?.[measure] || 0})`);

  document.getElementById("current-year").textContent = currentYear;
  drawHeatmapLegend(measure, currentYear);

};

function drawHeatmapLegend(measure, year) {
  const backgroundRect = heatmapLegendG.selectAll('rect').data([null]);
  backgroundRect
    .enter()
    .append('rect')
    .merge(backgroundRect)
    .attr('x', 10 * 2)
    .attr('y', 5)
    .attr('rx', 10 * 2)
    .attr('width', 100)
    .attr('fill', 'lightgray')
    .attr('height', 250);

  legendSvg.append('rect')
    .attr('x', 40)
    .attr('y', 0)
    .attr('width', 30)
    .attr('height', 200)
    .style('fill', 'url(#gradient)')
    .attr('transform', 'translate(0, 50)');

  // Draw the vertical axis using the scaleLinear
  let domain = d3.extent(Object.keys(statsData).map(country => {
    const englishName = countryMapping[country];
    return englishName ? statsData[country]?.[String(year)]?.[measure] || 0 : 0;
  }));
  let yAxisScale = d3.scaleSequential(d3.interpolateReds).domain(domain).range([200, 0]);
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
    console.error("Некорректная шкала оси!");
    return;
  }
  const yAxis = d3.axisRight(yAxisScale).ticks(5);
  removeElementIfExists('legend-axis');
  legendSvg.append('g')
    .attr('id', 'legend-axis')
    .attr('transform', 'translate(75, 50) scale(1)')
    .call(yAxis);
  removeElementIfExists('legend-axis-title');
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
    // unselect all currently selected countries except the clicked one
    for (const key in selectedCountries) {
      if (key != countryName) {
        unhighlightCountry(key);
        delete selectedCountries[key]
      }
    }
  }

  if (selectedCountries[countryName]) {
    // clicked country was already selected
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
};

const toggleAutoplay = () => {
  autoplay = !autoplay;
  document.getElementById("play-toggle").textContent = autoplay ? "Pause" : "Play";
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