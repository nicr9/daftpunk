// Create the Google Map…
var map = new google.maps.Map(d3.select("#map").node(), {
  zoom: 14,
  center: new google.maps.LatLng(53.3198638, -6.2578955),
  mapTypeId: google.maps.MapTypeId.TERRAIN
});

d3.json('properties', function(data) {
  var overlay = new google.maps.OverlayView();

  var priceList = [];
  for (var i = 0; i < data.length; i++) {
    if(data[i])
      priceList.push(data[i].current_price);
  };

  var color = d3.scale.linear().domain(priceList).range(["#00f","#f00"]);

  // Add the container when the overlay is added to the map.
  overlay.onAdd = function() {
    var layer = d3.select(this.getPanes().overlayMouseTarget).append("div")
      .attr("class", "gaffs");

    // Draw each marker as a separate SVG element.
    // We could use a single SVG, but what size would it have?
    overlay.draw = function() {
      var projection = this.getProjection(),
        padding = 100;

      var marker = layer.selectAll("svg")
        .data(d3.entries(data))
        .each(transform) // update existing markers
        .enter().append("svg:svg")
        .each(transform)
        .attr("class", "marker");

      // Add a circle.
      marker.append("svg:circle")
        .attr("r", 10)
        .attr("fill", function(d){ 
          console.log(color(d.value.current_price));
          return color(d.value.current_price);
        })
        .attr("cx", padding)
        .attr("cy", padding)
        .on("click", function(d){ 
          d3.json('property/' + d.value.id, function(res){
            
            alert(res.description);
          });
        });

      // Add a label.
      marker.append("svg:text")
        .attr("x", padding + 7)
        .attr("y", padding)
        .attr("dy", ".31em")
        // .style("visibility", "hidden")
        .text(function(d) {
          return d.value.current_price;
        });

      function transform(d) {
        d = d.value;
        d = new google.maps.LatLng(d.lat, d.long);
        d = projection.fromLatLngToDivPixel(d);
        return d3.select(this)
          .style("left", (d.x - padding) + "px")
          .style("top", (d.y - padding) + "px");
      }
    };
  };

  overlay.setMap(map);
});