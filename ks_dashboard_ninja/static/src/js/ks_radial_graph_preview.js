odoo.define('ks_dashboard_ninja.ks_radial_graph_preview', function(require) {
    "use strict";

    var registry = require('web.field_registry');
    var AbstractField = require('web.AbstractField');
    var core = require('web.core');

    var QWeb = core.qweb;
    var field_utils = require('web.field_utils');

    var Ks_radialBar_chart = AbstractField.extend({
       supportedFieldTypes: ['char'],
       resetOnAnyFieldChange: true,

        init: function(parent, state, params) {
            this._super.apply(this, arguments);
            var self =this;
            this.state = {};
        },

        _render: function() {
            if(this.root){
                this.root.dispose();
            }
            var self = this;
            this.$el.empty()
            var rec = self.recordData;
            if (rec.ks_dashboard_item_type === 'ks_radialBar_chart'){
                if(rec.ks_data_calculation_type !== "query"){
                    if (rec.ks_model_id) {
                        if (rec.ks_chart_groupby_type == 'date_type' && !rec.ks_chart_date_groupby) {
                            return this.$el.append($('<div>').text("Select Group by date to create chart based on date groupby"));
                        } else if (rec.ks_chart_data_count_type === "count" && !rec.ks_chart_relation_groupby) {
                            this.$el.append($('<div>').text("Select Group By to create chart view"));
                        } else if (rec.ks_chart_data_count_type !== "count" && (rec.ks_chart_measure_field.count === 0 || !rec.ks_chart_relation_groupby)) {
                            this.$el.append($('<div>').text("Select Measure and Group By to create chart view"));
                        } else if (!rec.ks_chart_data_count_type) {
                            this.$el.append($('<div>').text("Select Chart Data Count Type"));
                        } else {
                            this._GetRadialData(rec);
                        }
                    } else {
                        this.$el.append($('<div>').text("Select a Model first."));
                    }
                }else if(rec.ks_data_calculation_type === "query" && rec.ks_query_result) {
                    if(rec.ks_xlabels && rec.ks_ylabels){
                            this._GetRadialData(rec);
                    } else {
                        this.$el.append($('<div>').text("Please choose the X-labels and Y-labels"));
                    }
                }else {
                        this.$el.append($('<div>').text("Please run the appropriate Query"));
                }
            }
        },

        _GetRadialData: function(rec) {
            var self = this;
            self.shouldRenderChart = true;
            var field = this.recordData;
            var ks_chart_name;
            if (field.name) ks_chart_name = field.name;
            else if (field.ks_model_name) ks_chart_name = field.ks_model_id.data.display_name;
            else ks_chart_name = "Name";
            if(this.$el.find(".radial_text").length){
                this.$el.find(".radial_text").remove();
            }
            const chart_data = JSON.parse(rec.ks_chart_data);

            var ks_labels = chart_data['labels'];
            var ks_data=[];
            let data = [];
            if (chart_data.datasets){
                for (let i=0 ; i<chart_data.datasets.length ; i++){
                    ks_data.push({"ks_data":chart_data.datasets[i].data});
                }
            }
            if (ks_data.length){
                for (let i=0 ; i<chart_data.datasets.length ; i++){
                    ks_data.push({"ks_data":chart_data.datasets[i].data});
                    for (let j=0 ; j<ks_labels.length ; j++){
                        if (data.length != 0){
                            if (data[j]){
                                data[j][`value${i+1}`] = ks_data[i].ks_data[j]
                            }else{
                                let new_data = {};
                                new_data['category'] = ks_labels[j];
                                new_data[`value${i+1}`] = ks_data[i].ks_data[j];
                                data.push(new_data)
                            }
                        }else{
                            let new_data = {};
                            new_data['category'] = ks_labels[j];
                            new_data[`value${i+1}`] = ks_data[i].ks_data[j];
                            data.push(new_data)
                        }
                    }
                }
                var $chartContainer = $(QWeb.render('ks_dashboard_ninja.KsRadialBarChart', {
                    ks_chart_name: ks_chart_name
                }));
                this.$el.append($chartContainer);

                this.root = am5.Root.new(this.$el[0].firstChild);
                const theme = rec.ks_radial_item_color
                switch(theme){
                    case "default":
                        this.root.setThemes([am5themes_Animated.new(this.root)]);
                        break;
                    case "dark":
                        this.root.setThemes([am5themes_Dataviz.new(this.root)]);
                        break;
                    case "material":
                        this.root.setThemes([am5themes_Material.new(this.root)]);
                        break;
                    case "moonrise":
                        this.root.setThemes([am5themes_Moonrise.new(this.root)]);
                        break;
                    };


                // Create chart
                var chart = this.root.container.children.push(am5radar.RadarChart.new(this.root, {
                  panX: false,
                  panY: false,
                  wheelX: "panX",
                  wheelY: "zoomX",
                }));

                // Add cursor
    //            var cursor = chart.set("cursor", am5radar.RadarCursor.new(this.root, {
    //              behavior: "zoomX"
    //            }));
    //
    //            cursor.lineY.set("visible", false);

                // Create axes and their renderers
                var xRenderer = am5radar.AxisRendererCircular.new(this.root, {
                  strokeOpacity: 0.1,
                  minGridDistance: 50
                });

                xRenderer.labels.template.setAll({
                  radius: 25,
                  maxPosition: 0.98
                });

                var xAxis = chart.xAxes.push(am5xy.ValueAxis.new(this.root, {
                  renderer: xRenderer,
                  extraMax: 0.1,
                  tooltip: am5.Tooltip.new(this.root, {})
                }));

                var yAxis = chart.yAxes.push(am5xy.CategoryAxis.new(this.root, {
                  categoryField: "category",
                  renderer: am5radar.AxisRendererRadial.new(this.root, { minGridDistance: 20 })
                }));
                yAxis.get("renderer").labels.template.setAll({
                   oversizedBehavior: "truncate",
                   textAlign: "center",
                   maxWidth: 100,
                   ellipsis: "..."
                });

                // Create series
                for (var i = 0; i <chart_data.datasets.length; i++) {
                  var series = chart.series.push(am5radar.RadarColumnSeries.new(this.root, {
                    stacked: true,
                    name:`${chart_data.datasets[i].label}`,
                    xAxis: xAxis,
                    yAxis: yAxis,
                    valueXField: `value${i+1}`,
                    categoryYField: "category"
                  }));

                  series.set("stroke",this.root.interfaceColors.get("background"));
                  series.columns.template.setAll({
                    width: am5.p100,
                    strokeOpacity: 0.1,
                    tooltipText: "{name}: {valueX}  {category}"
                  });

                  series.data.setAll(data);
                  series.appear(1000);
                }

                var legend = chart.children.push(
                    am5.Legend.new(this.root, {
                        centerX: am5.percent(100),
                        x: am5.percent(100),
                        layout: this.root.verticalLayout
                    })
                );

                if(rec.ks_radial_legend==true){
                    legend.data.setAll(chart.series.values);
                }

                if (rec.ks_show_data_value == true){
                    var cursor = chart.set("cursor", am5xy.XYCursor.new(this.root, {}));
                }

                yAxis.data.setAll(data);

                // Animate chart and series in
                chart.appear(1000, 100);
            }else{
                  this.$el.append($("<div class='radial_text'>").text("No Data Available."));
            }
        },
    });
    registry.add('ks_dashboard_radial_chart', Ks_radialBar_chart);

    return {
        Ks_radialBar_chart: Ks_radialBar_chart,
    };
});
