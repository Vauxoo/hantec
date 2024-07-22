odoo.define('ks_dashboard_ninja.ks_bullet_chart', function(require) {
    "use strict";

    var registry = require('web.field_registry');
    var AbstractField = require('web.AbstractField');
    var core = require('web.core');

    var QWeb = core.qweb;
    var field_utils = require('web.field_utils');

    var ks_bullet_chart = AbstractField.extend({
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
            if (rec.ks_dashboard_item_type === 'ks_bullet_chart'){
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
                            this.get_bullet_chart(rec);
                        }
                    } else {
                        this.$el.append($('<div>').text("Select a Model first."));
                    }
                }else if(rec.ks_data_calculation_type === "query" && rec.ks_query_result) {
                    if(rec.ks_xlabels && rec.ks_ylabels){
                            this.get_flower_data(rec);
                    } else {
                        this.$el.append($('<div>').text("Please choose the X-labels and Y-labels"));
                    }
                }else {
                        this.$el.append($('<div>').text("Please run the appropriate Query"));
                }
            }
        },

        get_bullet_chart: function(rec) {
            var self = this;
            self.shouldRenderChart = true;
            var field = this.recordData;
            var ks_chart_name;
            if (field.name) ks_chart_name = field.name;
            else if (field.ks_model_name) ks_chart_name = field.ks_model_id.data.display_name;
            else ks_chart_name = "Name";
            if(this.$el.find(".funnel_text").length){
                this.$el.find(".funnel_text").remove();
            }
            const chart_data = JSON.parse(rec.ks_chart_data);
            var ks_labels = chart_data['labels'];
            var ks_data = chart_data.datasets;

            let data=[];
            if (ks_data.length){
                for (let i=0 ; i<ks_labels.length ; i++){
                    let data2={};
                    for (let j=0 ;j<ks_data.length ; j++){
                        data2[`value${j+1}`] = ks_data[j].data[i]
                    }
                    data2["category"] = ks_labels[i]
                    data.push(data2)
                }

                var $chartContainer = $(QWeb.render('ks_dashboard_ninja.ksbulletchart', {
                    ks_chart_name: ks_chart_name
                }));
                this.$el.append($chartContainer);
                // Create root and chart
                this.root = am5.Root.new(this.$el[0].firstChild);
                const theme = rec.ks_funnel_item_color
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

                var chart = this.root.container.children.push(am5xy.XYChart.new(this.root, {
                panX: true,
                panY: false,
                wheelX: "panX",
                wheelY: "zoomX",
                layout: this.root.verticalLayout
                }));


                // Create axes

                var xRenderer = am5xy.AxisRendererX.new(this.root, {
                minGridDistance: 70
                });

                var xAxis = chart.xAxes.push(am5xy.CategoryAxis.new(this.root, {
                categoryField: "category",
                renderer: xRenderer,
                tooltip: am5.Tooltip.new(this.root, {
                themeTags: ["axis"],
                animationDuration: 200
                })
                }));

                xRenderer.grid.template.setAll({
                location: 1
                })

                xAxis.data.setAll(data);
                xAxis.get("renderer").labels.template.setAll({
                  oversizedBehavior: "wrap",
                  maxWidth: 100,
                  textAlign: "center"
                });


                var yAxis = chart.yAxes.push(am5xy.ValueAxis.new(this.root, {
                 min: 0,
                renderer: am5xy.AxisRendererY.new(this.root, {
                strokeOpacity: 0.1
                })
                }));

                // Add series

                for (let k = 0;k<ks_data.length ; k++){
                    var series = chart.series.push(am5xy.ColumnSeries.new(this.root, {
                    name: `${ks_data[k].label}`,
                    xAxis: xAxis,
                    yAxis: yAxis,
                    valueYField:`value${k+1}`,
                    categoryXField: "category",
                    clustered: false,
                    tooltip: am5.Tooltip.new(this.root, {
                    labelText: `${ks_data[k].label}: {valueY}`
                    })
                    }));

                    series.columns.template.setAll({
                    width: am5.percent(80-(10*k)),
                    tooltipY: 0,
                    strokeOpacity: 0
                    });
                    series.data.setAll(data);
                }

                var legend = chart.children.unshift(am5.Legend.new(this.root, {
                centerX: am5.p50,
                x: am5.p50,
                marginTop: 15,
                marginBottom: 15
                }));

                if(rec.ks_hide_legend==true){
                    legend.data.setAll(chart.series.values);
                }

                if (rec.ks_show_data_value == true){
                    var cursor = chart.set("cursor", am5xy.XYCursor.new(this.root, {}));
                }
                var cursor = chart.set("cursor", am5xy.XYCursor.new(this.root, {
                    behavior: "none"
                    })
                );
                cursor.lineY.set("visible", false);
                cursor.lineX.set("visible", false);


                chart.appear(1000, 100);
                series.appear();
            }else{
                this.$el.append($("<div class='funnel_text'>").text("No Data Available."));
            }
        },
    });
    registry.add('ks_dashboard_bullet_chart', ks_bullet_chart);

    return {
        ks_bullet_chart: ks_bullet_chart,
    };
});
