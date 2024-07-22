odoo.define('ks_dashboard_ninja.ks_funnel_chart', function(require) {
    "use strict";

    var registry = require('web.field_registry');
    var AbstractField = require('web.AbstractField');
    var core = require('web.core');

    var QWeb = core.qweb;
    var field_utils = require('web.field_utils');

    var ks_funnel_chart = AbstractField.extend({
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
            if (rec.ks_dashboard_item_type === 'ks_funnel_chart'){
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
                            this.get_funnel_chart(rec);
                        }
                    } else {
                        this.$el.append($('<div>').text("Select a Model first."));
                    }
                }else if(rec.ks_data_calculation_type === "query" && rec.ks_query_result) {
                    if(rec.ks_xlabels && rec.ks_ylabels){
                            this.get_funnel_chart(rec);
                    } else {
                        this.$el.append($('<div>').text("Please choose the X-labels and Y-labels"));
                    }
                }else {
                        this.$el.append($('<div>').text("Please run the appropriate Query"));
                }
            }
        },

        get_funnel_chart: function(rec) {
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
            var ks_data = chart_data.datasets[0].data;
            const ks_sortobj = Object.fromEntries(
                ks_labels.map((key, index) => [key, ks_data[index]]),
            );
            const keyValueArray = Object.entries(ks_sortobj);
            keyValueArray.sort((a, b) => b[1] - a[1]);

            var data=[];
            if (keyValueArray.length){
                for (let i=0 ; i<keyValueArray.length ; i++){
                    data.push({"stage":keyValueArray[i][0],"applicants":keyValueArray[i][1]})
                }
                var $chartContainer = $(QWeb.render('ks_dashboard_ninja.ksfunnelchart', {
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

                var chart = this.root.container.children.push(
                    am5percent.SlicedChart.new(this.root, {
                        layout: this.root.verticalLayout
                    })
                );

                // Create series
                var series = chart.series.push(
                    am5percent.FunnelSeries.new(this.root, {
                        alignLabels: false,
                        name: "Series",
                        valueField: "applicants",
                        categoryField: "stage",
                        orientation: "vertical",
                    })
                );

                series.data.setAll(data);
                series.appear(1000);

                if(rec.ks_show_data_value && rec.ks_data_label_type=="value"){
                    series.labels.template.set("text", "{category}: {value}");
                }else if(rec.ks_show_data_value && rec.ks_data_label_type=="percent"){
                    series.labels.template.set("text", "{category}: {valuePercentTotal.formatNumber('0.00')}%");
                }else{
                    series.ticks.template.set("forceHidden", true);
                }

                var legend = chart.children.push(am5.Legend.new(this.root, {
                    centerX: am5.p50,
                    x: am5.p50,
                    marginTop: 15,
                    marginBottom: 15,
                    layout: this.root.horizontalLayout,
                }));

                if(rec.ks_hide_legend==true){
                    legend.data.setAll(series.dataItems);
                }

                chart.appear(1000, 100);
            }else{
                $his.$el.append($("<div class='funnel_text'>").text("No Data Available."));
            }
        },
    });
    registry.add('ks_dashboard_funnel_chart', ks_funnel_chart);

    return {
        ks_funnel_chart: ks_funnel_chart,
    };
});
