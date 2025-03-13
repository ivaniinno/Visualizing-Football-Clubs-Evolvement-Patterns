const data = [
  {
    name: "Manchester United",
    playersInNationalTeams: { 2011: 15, 2012: 18, 2013: 20 },
    titles: { 2011: 66, 2012: 67, 2013: 70 },
    cups: 20,
    flag: "https://upload.wikimedia.org/wikipedia/en/7/7a/Manchester_United_FC_crest.svg"
  },
  {
    name: "Barcelona",
    playersInNationalTeams: { 2011: 14, 2012: 17, 2013: 19 },
    titles: { 2011: 75, 2012: 78, 2013: 80 },
    cups: 26,
    flag: "https://upload.wikimedia.org/wikipedia/en/4/47/FC_Barcelona_%28crest%29.svg"
  },
  {
    name: "Bayern Munich",
    playersInNationalTeams: { 2011: 13, 2012: 15, 2013: 18 },
    titles: { 2011: 55, 2012: 58, 2013: 63 },
    cups: 31,
    flag: "https://upload.wikimedia.org/wikipedia/commons/1/15/FC_Bayern_München_logo_%282017%29.svg"
  }
];

const years = [2011, 2012, 2013];
let currentYear = 2011;
let previousYear = 2011;
let selectedClub = null;
let previousSelectedClub = null;
let isTimelineRunning = false;

const width = 800;
const height = 600;
const margin = { top: 20, right: 20, bottom: 50, left: 50 };

const svg = d3
  .select("svg")
  .attr("width", width)
  .attr("height", height);

const xScale = d3.scaleLinear().domain([10, 25]).range([margin.left, width - margin.right]);
const yScale = d3.scaleLinear().domain([50, 85]).range([height - margin.bottom, margin.top]);

svg
  .append("g")
  .attr("transform", `translate(0, ${height - margin.bottom})`)
  .call(d3.axisBottom(xScale).ticks(5));

svg
  .append("g")
  .attr("transform", `translate(${margin.left}, 0)`)
  .call(d3.axisLeft(yScale).ticks(5));

const updateDashedLines = (d, year) => {
  svg.selectAll(".dashed-line").remove();

  svg
    .append("line")
    .attr("class", "dashed-line")
    .attr("x1", xScale(d.playersInNationalTeams[year]))
    .attr("x2", xScale(d.playersInNationalTeams[year]))
    .attr("y1", yScale(d.titles[year]))
    .attr("y2", height - margin.bottom)
    .attr("stroke", "black")
    .attr("stroke-dasharray", "5,5");

  svg
    .append("line")
    .attr("class", "dashed-line")
    .attr("x1", xScale(d.playersInNationalTeams[year]))
    .attr("x2", margin.left)
    .attr("y1", yScale(d.titles[year]))
    .attr("y2", yScale(d.titles[year]))
    .attr("stroke", "black")
    .attr("stroke-dasharray", "5,5");
};


const trajectoryContainer = svg.append("g").attr("class", "trajectory-container");

let trajectoryData = []; 


const drawCircles = (year) => {
  const circles = svg.selectAll("circle").data(data, (d) => d.name);

  circles
    .enter()
    .append("circle")
    .attr("cx", (d) => xScale(d.playersInNationalTeams[year]))
    .attr("cy", (d) => yScale(d.titles[year]))
    .attr("r", (d) => d.cups * 0.5)
    .attr("fill", "purple")
    .attr("stroke", "black")
    .attr("opacity", 0.8)
    .on("mouseover", function (event, d) {
      d3.select(this).attr("stroke", "orange").attr("stroke-width", 2);
      updateDashedLines(d, currentYear);

      const textPadding = 5;

      const tempText = svg
        .append("text")
        .attr("x", xScale(d.playersInNationalTeams[currentYear]))
        .attr("y", yScale(d.titles[currentYear]) - 20)
        .attr("text-anchor", "middle")
        .attr("font-size", "14px")
        .attr("font-weight", "bold")
        .attr("fill", "black")
        .text(d.name);

      const bbox = tempText.node().getBBox();

      svg
        .append("rect")
        .attr("class", "tooltip-bg")
        .attr("x", bbox.x - textPadding)
        .attr("y", bbox.y - textPadding)
        .attr("width", bbox.width + 2 * textPadding)
        .attr("height", bbox.height + 2 * textPadding)
        .attr("fill", "white")
        .attr("stroke", "black")
        .attr("rx", 4);

      tempText.raise();

  
      tempText.attr("class", "tooltip-text");
    })
    .on("mouseout", function () {
      d3.select(this).attr("stroke", "black").attr("stroke-width", 1);
      svg.selectAll(".dashed-line").remove();
      svg.selectAll(".tooltip-text").remove();
      svg.selectAll(".tooltip-bg").remove();
    })
    .on("click", function (event, d) {
      if(isTimelineRunning) return;

      previousSelectedClub = selectedClub;
      selectedClub = d;

      trajectoryData = years.map((year) => ({
        x: xScale(d.playersInNationalTeams[year]),
        y: yScale(d.titles[year]),
      }));

      if(selectedClub !== previousSelectedClub){
        trajectoryContainer.selectAll(".new-trajectory").remove();
        drawNewTrajectory(currentYear);
      }
      d3.select("#club-info").html(
        `<img src="${d.flag}" alt="${d.name} flag" style="width:100px; height:auto;">
        <h3>${d.name}</h3>
           <p>Players in National Teams: ${d.playersInNationalTeams[year]}</p>
           <p>Titles: ${d.titles[year]}</p>`
      );
      svg.selectAll("circle").attr("opacity", 0.2);
      d3.select(this).attr("opacity", 1);
    });

  circles
    .transition()
    .duration(1500)
    .attr("cx", (d) => xScale(d.playersInNationalTeams[year]))
    .attr("cy", (d) => yScale(d.titles[year]));

  circles.exit().remove();
};

svg.on("click", (event) => {
  if (event.target.tagName === "svg") {
    trajectoryContainer.selectAll("path").remove();
    svg.selectAll("circle").attr("opacity", 0.8);
  }
});


const drawNewTrajectory = (year) => {
  const partialData = trajectoryData.slice(0, years.indexOf(year) + 1);
  trajectoryContainer
    .append("path")
    .datum(partialData)
    .attr("class", "new-trajectory")
    .attr("fill", "none")
    .attr("stroke", "blue")
    .attr("stroke-width", 2)
    .attr("opacity", 0.6)
    .attr(
      "d",
      d3
        .line()
        .curve(d3.curveCatmullRom)
        .x((d) => d.x)
        .y((d) => d.y)
    );
}

const updateTrajectory = (year) => {

  if (trajectoryData.length === 0 || !selectedClub) return;

  if (previousYear > currentYear) {
    trajectoryContainer.selectAll(".new-trajectory").remove();
  }
  
  const partialData = trajectoryData.slice(years.indexOf(year-1), years.indexOf(year) + 1);

  const path = trajectoryContainer
    .append("path")
    .datum(partialData)
    .attr("class", "new-trajectory")
    .attr("fill", "none")
    .attr("stroke", "blue")
    .attr("stroke-width", 2)
    .attr("opacity", 0.6)
    .attr(
      "d",
      d3
        .line()
        .curve(d3.curveCatmullRom)
        .x((d) => d.x)
        .y((d) => d.y)
    );

  const totalLength = path.node().getTotalLength();

  path
    .attr("stroke-dasharray", `${totalLength},${totalLength}`)
    .attr("stroke-dashoffset", totalLength)
    .transition()
    .duration(1500)
    .attr("stroke-dashoffset", 0);
  
    previousYear = currentYear;
};

let interval;
const playPause = () => {
  if (interval) {
    clearInterval(interval);
    interval = null;
    isTimelineRunning = false;
    d3.select("#play-pause").text("Play");
  } else {
    isTimelineRunning = true;
    interval = setInterval(() => {
      currentYear = currentYear < 2013 ? currentYear + 1 : 2011;
      drawCircles(currentYear);
      updateTrajectory(currentYear); 
      d3.select("#year-display").text(currentYear);
    }, 2000);
    d3.select("#play-pause").text("Pause");
  }
};

d3.select("#play-pause").on("click", playPause);
d3.select("#year-display").text(currentYear);

drawCircles(currentYear);
