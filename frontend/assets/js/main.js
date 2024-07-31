// Set global variables based on dev or prod
var strHost = $(location).attr('host');

if (strHost.includes('dev') || strHost.includes('127.0.0.1') || strHost.includes('localhost')) {
    console.log("In debug mode");
    var apiUrl = "https://93iuio76jk.execute-api.ap-southeast-2.amazonaws.com/Prod";
    var DEBUG = true;

} else {
    var apiUrl = "https://d1xu0sn87l.execute-api.ap-southeast-2.amazonaws.com/Prod";
}

// Events below here
$(document).ready(function () {
    var strPath = $(location).attr('pathname');
    var path = strPath.split("/");

    if (DEBUG) {
        console.log(path);
    }

    if (path[1] == "region_compare") 
    {
        selects = ["strRegion1","strRegion2","strRegion3"]
        getRegions(selects);
        currentVersion = getCurrentVersion();
        getServicesList(currentVersion);
        
    } 
    else if (path[1] == "service_gossip") 
    {
        getServiceGossip();
    } 
    else if (path[1] == "service_list") 
    {
        selects = ["strRegion"]
        getRegions(selects);
    } 
    else if (path[1] == "release_notes") 
    {
        // Do nothing
    } 
    else if (path[1] == "tool_kit" && path[2] == "llm_compare") 
    {
        var llmsByRegion = "";
        $("#divStatus").removeClass("d-none");
        $("#divStatus_content").removeClass("d-none");
        getLLMList();
    } 
    else 
    {
        $("#divStatus").removeClass("d-none");
        getNews();
    }
});

$("#strRegion").on("change", function() {
    var region = $(this).val();
    $("#divStatus").removeClass("d-none");
    getServicesByRegion(region, 0);
})

$("#strRegion1").on("change", function() {
    var region = $(this).val();
    getServicesByRegion(region, 1);
})

$("#strRegion2").on("change", function() {
    var region = $(this).val();
    getServicesByRegion(region, 2);
})

$("#strRegion3").on("change", function() {
    var region = $(this).val();
    getServicesByRegion(region, 3);
})

$("#strLLMRegion1").on("change", function() {
    var region = $(this).val();
    getLLMByRegion(region, 1);
})

$("#strLLMRegion2").on("change", function() {
    var region = $(this).val();
    getLLMByRegion(region, 2);
})

$("#strLLMRegion3").on("change", function() {
    var region = $(this).val();
    getLLMByRegion(region, 3);
})
// End events

// Functions below here
function _templateFunction() {

    $.ajax({
        type: "GET",
        url: apiUrl + "/_template",
        headers: {
            'Access-Control-Allow-Origin': "*",
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'        
        },
        crossDomain: true,
        dataType: "json",
        success: function(data) {
            if (DEBUG) {
                console.log(data);
            }
        
            // Logic here ...
        }
    })
}

function getServicesListAsJson() {

    return $.ajax({
        type: "GET",
        url: "/data/services.json",
        headers: {
            'Access-Control-Allow-Origin': "*",
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        crossDomain: true,
        dataType: "json",
        success: function(data) {
            if (DEBUG) {
                console.log("getServicesListAsJson success");
            }
            
            return data;
        }
    });

    
}

function getRegions(selects) {

    $.ajax({
        type: "GET",
        url: apiUrl + "/regions",
        headers: {
            'Access-Control-Allow-Origin': "*",
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'        
        },
        crossDomain: true,
        dataType: "json",
        success: function(data) {
            if (DEBUG) {
                console.log(data);
            }
            
            for (var i = 0; i < selects.length; i++) {

                // var continents = {};
                // $.each(data['region_data'], function(data_key, data_value) {
                //     if (continents[data_value['continent']] == undefined) {
                //         continents[data_value['continent']] = [];
                //     }
                //     continents[data_value['continent']].push(data_value['id']);
                //     var optgroup = $('<optgroup>')
                //         .attr('label', data_value['continent']);
                //     $.each(continents[data_value['continent']], function(key, value) {
                //         optgroup.append($("<option></option>")
                //             .attr("value", value).text(data_value['name'] + " (" + value + ")"));
                //     });
                //     $("#" + selects[i]).append(optgroup);
                // });
                
                var $el = $("#" + selects[i]);
                $el.empty();
                $el.append($("<option disabled selected></option>")
                    .attr("value", "").text("Select a region"));
                $.each(data['regions'], function(key, value) {
                    $.each(data['region_data'], function(data_key, data_value) {
                        if (data_value['id'] == value) {
                            $el.append($("<option></option>")
                            .attr("value", value).text(data_value['continent'] + " (" + data_value['name'] + ") - " + value));
                            }
                    });
                });
            }            
        },
        error: function(data) {
            alert('Error');
            console.log(data);
        }
    })
}

function getServicesByRegion(region, index) {

    let services = getServicesListAsJson();

    $.ajax({
        type: "GET",
        url: apiUrl + "/services/" + region,
        headers: {
            'Access-Control-Allow-Origin': "*",
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'        
        },
        crossDomain: true,
        dataType: "json",
        success: function(data) {

            if (index == 0) {

                var version = data['version']
                var version_date_year = version.substring(0, 4);
                var version_date_month = version.substring(4, 6);
                var version_date_day = version.substring(6, 8);
                var version_date = version_date_year + "-" + version_date_month + "-" + version_date_day;
                count = 0;
                var $el = $("#tbodyServicesByRegion");
                $el.empty();
                $.each(data['services'], function(key,value) {
                    count = count + 1;
                    if(count % 2 == 0) {
                        $el.append("<tr class=\"table-secondary\"><th scope=\"row\">" + value.attributes["aws:serviceName"] + "</th><td><a href=\"" + value.attributes["aws:serviceUrl"] + "\">Link</a></td></tr>");
                    } else {
                        $el.append("<tr class=\"table-primary\"><th scope=\"row\">" + value.attributes["aws:serviceName"] + "</th><td><a href=\"" + value.attributes["aws:serviceUrl"] + "\">Link</a></td></tr>");                
                    }
                }); 
                
                var $el = $("#divServicesByRegionCount");
                $el.empty();
                $el.append("<table class=\"table table-hover\" id=\"tableServicesByRegion\"><tr><th scope=\"row\">Total AWS Services Available</th><td>" + count + "</td></tr><tr><th>Last Updated</td><td>" +  version_date + "</td></tr></table>");
                
                $("#divServicesByRegion").removeClass("d-none");
                $("#divServicesByRegionCount").removeClass("d-none");
                $("#divStatus").addClass("d-none");
            } else {
                region_list = [];
                
                service_list = services.responseJSON;
                if (DEBUG) {
                    console.log(service_list);
                }
                $.each(data['services'], function(key, value) {
                    region_list.push(value.attributes['aws:serviceName']);
                })

                $.each(service_list, function(key, value) {
                    var $el = $("#region" + index + "_" + key);
                    $el.empty();

                    if (region_list.includes(value)) {
                        $el.append("<img src=\"/assets/icons/check-square-fill.svg\">");
                    }
                })
            }
        }
    })
}

function getCurrentVersion() {

    $.ajax({
        type: "GET",
        url: apiUrl + "/version",
        headers: {
            'Access-Control-Allow-Origin': "*",
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        crossDomain: true,
        dataType: "json",
        success: function(data) {
            return data['version'];
        }
    });

}

function getServicesList() {

    $.ajax({
        type: "GET",
        url: "/data/services.json",
        headers: {
            'Access-Control-Allow-Origin': "*",
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        crossDomain: true,
        dataType: "json",
        success: function(data) {
            
            count = 0;

            var $el = $("#tbodyServicesCompare");
            $el.empty();
            $.each(data, function(key, value) {
                count = count + 1;
                if (count % 2 == 0) {
                    $el.append("<tr class=\"table-secondary\"><th scope=\"row\">" + value + "</th><td id=region1_" + key + "></td><td id=region2_" + key + "></td><td id=region3_" + key + "></td></tr>");    
                } else {
                    $el.append("<tr class=\"table-primary\"><th scope=\"row\">" + value + "</th><td id=region1_" + key + "></td><td id=region2_" + key + "></td><td id=region3_" + key + "></td></tr>");
                }
                
            });
        }
    });
}

function getServiceGossip() {

    var latest_gossip = "";

    $.ajax({
        type: "GET",
        url: "/data/gossip.json",
        headers: {
            'Access-Control-Allow-Origin': "*",
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        crossDomain: true,
        dataType: "json",
        success: function(data) {
            $.each(data, function(key, value) {
                if (DEBUG) {
                    console.log(value);
                }
                date = value['timestamp'].split("T")[0];
                time = value['timestamp'].split("T")[1].split(".")[0];
                latest_gossip = "[" + date + " " + time + "]" + value['push_msg'] + "\n" + latest_gossip
            });
            $el = $("#serviceGossip");
            $el.val(latest_gossip);
        },
        error: function(data) {
            alert('error');
            console.log(data);
        }
    });
}

function getNews() {
    $.ajax({
        type: "GET",
        url: apiUrl + "/news",
        headers: {
            'Access-Control-Allow-Origin': "*",
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        crossDomain: true,
        dataType: "json",
        success: function(data) {
            
            $("#divStatus").addClass("d-none");
            $el = $("#divServiceNews");
            $.each(data['items'], function(key, value) {
                if (DEBUG) {
                    console.log(value);
                }
                
                var news_story = `
                <div class="card border-primary mb-3">
                <div class="card-header">` + value['service'] + `</div>
                <div class="card-body">
                  <h4 class="card-title">` + value['headline'] + `</h4>
                  <p class="card-text">` + value['announcement'] + `</p>`;
                
                $.each(value['resources'], function(resources_key, resources_value) {
                    news_story = news_story + `<a href="` + resources_value['url'] + `" class="card-link">` + resources_value['title'] + `</a><br />`;
                });

                news_story = news_story + `
                </div>
                <div class="card-footer">` + value['date_announced'] + `</div>
              </div>                
                `;
                $el.append(news_story);
            });
        },
        error: function(data) {
            alert('error');
            console.log(data);
        }
    });
}

function getLLMList() {
    $.ajax({
        type: "GET",
        url: "/data/models/latest.json",
        headers: {
            'Access-Control-Allow-Origin': "*",
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        crossDomain: true,
        dataType: "json",
        success: function(data) {
            if (DEBUG) {
                console.log(data);
            }

            var count = 0;
            selects = ["strLLMRegion1","strLLMRegion2","strLLMRegion3"]

            // Populate the region selects (selects = ["strRegion1","strRegion2","strRegion3"])
            for (var i = 0; i < selects.length; i++) {
                
                var $el = $("#" + selects[i]);
                $el.empty();
                $el.append($("<option disabled selected></option>")
                    .attr("value", "").text("Select a region"));
                $.each(data['regions_data'], function(key, value) {
                    $el.append($("<option></option>")
                    .attr("value", value['id']).text(value['continent'] + " (" + value['name'] + ") - " + value['id']));
                });
            }            

            // Populate LLM list
            var $el = $("#tbodyLLMCompare");
            $el.empty();
            $.each(data['unique_model_list'], function(key, value) {
                count = count + 1;
                var strDomId = value[1].replace(/\W/g, '');
                if (count % 2 == 0) {
                    $el.append("<tr class=\"table-secondary\"><td scope=\"row\"><b>" + value[0] + "</b><br /><span style=\"font-family:'Courier New'\">" + value[1] + "</span></td><td id=\"region1_" + strDomId + "\"></td><td id=\"region2_" + strDomId + "\"></td><td id=\"region3_" + strDomId + "\"></td></tr>");
                } else {
                    $el.append("<tr class=\"table-primary\"><td scope=\"row\"><b>" + value[0] + "</b><br /><span style=\"font-family:'Courier New'\">" + value[1] + "</span></td><td id=\"region1_" + strDomId + "\"></td><td id=\"region2_" + strDomId + "\"></td><td id=\"region3_" + strDomId + "\"></td></tr>");
                }
            });

            $("#divStatus").addClass("d-none");
            $("#divStatus_content").addClass("d-none");
            $("#divLLMCompare").removeClass("d-none");

            llmsByRegion = data['model_by_region'];

        },
        error: function(data) {
            alert('error');
            console.log(data);
        }
    });
}

function getLLMByRegion(region, index) {

    $("[id^=region" + index + "_]").empty();

    $.each(llmsByRegion, function(key, value) {
        if (region == value['region']) {
            var llms = value['llms'];
        }
        $.each(llms, function(key, value) {
            // console.log("--- LLMS " + region + "---");
            // console.log(value['modelId']);
            
            var strDomId = value['modelId'].replace(/\W/g, '');
            // console.log(strDomId);
            var $el = $("#region" + index + "_" + strDomId);
    
            $el.empty();
            $el.append("<img src=\"/assets/icons/check-square-fill.svg\">");
    
        });
    
    });

}

// End functions