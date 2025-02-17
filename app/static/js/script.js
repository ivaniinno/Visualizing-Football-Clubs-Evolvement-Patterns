console.log("D3 version:", d3.version);

d3.json("/data").then(data => {
    createVisualization(data);
});

function createVisualization(data) {
    const svg = d3.select("#visualization")
        .append("svg")
        .attr("width", 800)
        .attr("height", 600);

    svg.selectAll("circle")
        .data(data)
        .enter()
        .append("circle")
        .attr("cx", d => d.x)
        .attr("cy", d => d.y)
        .attr("r", 5)
        .attr("fill", "steelblue");
}