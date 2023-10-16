
let timer = null;
let select_stock_price = 0;
let mybalance = 0;
let inventory_list = [];
var k_line_chart = klinecharts.init('k_line_chart')
var updtime = 0;
var timeinv;
var stockCode = undefined;
var timerange = "1d";
var intenvel = "1m";
var nowcurrency = "TWD";
ssn = new SlimSelect({
    select: '#inputStockCode',
    settings: {
        placeholderText: '查詢股票代碼',
        searchText: '找不到股票代碼',
    },
    timeout: 500,
    events: {
        afterChange: (select = undefined, defa = undefined) => {
            window.scrollTo(0, 0);
            try {
                stockCode = defa || select[0].value;
            } catch (error) {
            }
            console.log(stockCode, defa);

            $("#btn_get_stock_info").attr("disabled", true);
            $("#btn_sw").attr("disabled", true);
            $("#inp_count").attr("disabled", true);
            $("#btn_buy").attr("disabled", true);
            $("#btn_get_stock_info").html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 取得現價中...')
            $.ajax({
                url: "/stock_info",
                type: "POST",
                data: {
                    stock: stockCode,
                    timerange: timerange,
                    intenvel: intenvel
                },
                success: function (data) {
                    console.log(data);
                    $('#select_stock_name').html(data.name + "<p class='text-primary name_p'>" + data.price + " <small>" + data.currency + "</small></p><p class='text-success name_p' id='twdprice'></p>");

                    if (data.currency != 'TWD') {
                        $.ajax({
                            url: "/getrate",
                            type: "POST",
                            data: {
                                fromex: data.currency,
                                toex: 'TWD',
                                price: data.price
                            },
                            success: function (data) {
                                // $('#select_stock_name').html($('#select_stock_name').html() + "<p class='text-primary name_p'>TWD$" + parseFloat(data.price).toFixed(2) + "</p>");
                                $('#twdprice').html(parseFloat(data.price).toFixed(2) + "<small> TWD</small>");
                                select_stock_price = data.price;
                                $("#calc_cost").html("預計花費 : " + (select_stock_price * $("#inp_count").val()).toFixed(2) + "元");
                                $('#calc_balance').html("預計餘額 : " + (mybalance - (select_stock_price * $("#inp_count").val()).toFixed(2)).toFixed(2) + "元");
                                if (mybalance - (select_stock_price * $("#inp_count").val()).toFixed(2) < 0) {
                                    $('#calc_balance').addClass('text-danger');
                                    $("#btn_buy").attr("disabled", true);
                                }
                                else {
                                    $('#calc_balance').removeClass('text-danger');
                                    $("#btn_buy").attr("disabled", false);
                                }
                                nowcurrency = data.currency;
                            }
                        });

                    } else {
                        select_stock_price = data.price;
                        $("#calc_cost").html("預計花費 : " + (select_stock_price * $("#inp_count").val()).toFixed(2) * 1000 + "元");
                        $('#calc_balance').html("預計餘額 : " + (mybalance - (select_stock_price * $("#inp_count").val()).toFixed(2) * 1000).toFixed(2) + "元");


                        if (mybalance - (select_stock_price * $("#inp_count").val()).toFixed(2) * 1000 < 0) {
                            $('#calc_balance').addClass('text-danger');
                            $("#btn_buy").attr("disabled", true);
                        } else {
                            $('#calc_balance').removeClass('text-danger');
                            $("#btn_buy").attr("disabled", false);
                        }
                        nowcurrency = 'TWD';
                    }
                    //percentage
                    if (data.percentage < 0) {
                        $('#select_stock_name').html($('#select_stock_name').html() + "<p class='text-success name_p'>▼" + data.percentage + "</p>");
                    }
                    else {
                        $('#select_stock_name').html($('#select_stock_name').html() + "<p class='text-danger name_p'>▲" + data.percentage + "</p>");
                    }

                    $("#btn_get_stock_info").attr("disabled", false);
                    $("#btn_get_stock_info").html('取得現價')

                    $("#btn_get_stock_info").attr("disabled", false);
                    $("#btn_sw").attr("disabled", false);
                    $("#inp_count").attr("disabled", false);
                    $("#btn_buy").attr("disabled", false);


                    //parse data.stamp_data from {0: , 1: , 2: , ...} to [{},{},{}]
                    let stamp_data = [];
                    for (let i = 0; i < data.stamp_data.length; i++) {
                        //parse  timestamp
                        stamp_data.push(data.stamp_data[i]);
                    }
                    k_line_chart.applyNewData(stamp_data);
                    updtime = new Date().getTime();
                    timeinv = setInterval(() => {
                        $("#btn_get_stock_info").text('取得現價 (' + (parseInt(60 - (new Date().getTime() - updtime) / 1000)) + '秒後更新)');
                        if (new Date().getTime() - updtime > 60000) {
                            clearInterval(timeinv);
                            $("btn_get_stock_info").html('取得現價 (等待更新)');
                            ssn.events.afterChange();

                        }
                    }, 1000);

                },
                error: function (err) {
                    alert("圖表不可用");
                    intenvel = "1m";
                    timerange = "1d";
                    $(".dropdown-menu li a").parents('.btn-group').find('.dropdown-toggle').text("Intenvel " + "1m");
                    $("#btn_get_stock_info").attr("disabled", false);
                    $("#btn_get_stock_info").html('取得現價')

                    $("#btn_get_stock_info").attr("disabled", false);
                    $("#btn_sw").attr("disabled", false);
                    $("#inp_count").attr("disabled", false);
                    $("#btn_buy").attr("disabled", false);
                    select_stock_price = data.price;
                    $("#calc_cost").html("預計花費 : " + (select_stock_price * $("#inp_count").val()).toFixed(2) * 1000 + "元");
                    $('#calc_balance').html("預計餘額 : " + (mybalance - (select_stock_price * $("#inp_count").val()).toFixed(2) * 1000).toFixed(2) + "元");
                    if (mybalance - (select_stock_price * $("#inp_count").val()).toFixed(2) * 1000 < 0) {
                        $('#calc_balance').addClass('text-danger');
                        $("#btn_buy").attr("disabled", true);
                    }


                }
            })
        },
        search: (search, currentData) => {
            if (search.length < 1) {
                timer && clearTimeout(timer);
                return Promise.resolve(currentData);
            }
            return new Promise((resolve, reject) => {


                timer && clearTimeout(timer);
                timer = setTimeout(() => {
                    $.ajax({
                        url: "/search_stock",
                        type: "POST",
                        data: {
                            stock: search
                        },
                        success: function (data) {
                            let option = data.map((item) => {
                                return { 'text': item }
                            })
                            resolve(option);
                        },
                        error: function (err) {
                            console.log(err);
                            reject(err);
                        }
                    })
                }, 500)
            })

        }

    }
})

isbuy = true;
$('#btn_sw').on('click', function () {
    if (isbuy) {
        $(this).removeClass('btn-success');
        $(this).addClass('btn-danger');
        $('#btn_sw').text('賣出 (切換)');
    } else {
        $(this).removeClass('btn-danger');
        $(this).addClass('btn-success');
        $('#btn_sw').text('買進 (切換)');
    }
    isbuy = !isbuy;
    if (isbuy) {
        if (nowcurrency != 'TWD') {
            $("#calc_cost").html("預計花費 : " + (select_stock_price * $("#inp_count").val()).toFixed(2) + "元");
            $('#calc_balance').html("預計餘額 : " + (mybalance - (select_stock_price * $("#inp_count").val()).toFixed(2)).toFixed(2) + "元");
            if (mybalance - (select_stock_price * $("#inp_count").val()).toFixed(2) < 0) {
                $('#calc_balance').addClass('text-danger');
                $("#btn_buy").attr("disabled", true);
            } else {
                $('#calc_balance').removeClass('text-danger');
                $("#btn_buy").attr("disabled", false);
            }
        } else {
            $("#calc_cost").html("預計花費 : " + (select_stock_price * $("#inp_count").val()).toFixed(2) * 1000 + "元");
            $('#calc_balance').html("預計餘額 : " + (mybalance - (select_stock_price * $("#inp_count").val()).toFixed(2) * 1000).toFixed(2) + "元");
            if (mybalance - (select_stock_price * $("#inp_count").val()).toFixed(2) * 1000 < 0) {
                $('#calc_balance').addClass('text-danger');
                $("#btn_buy").attr("disabled", true);
            }
            else {
                $('#calc_balance').removeClass('text-danger');
                $("#btn_buy").attr("disabled", false);
            }
        }
    }
    else {
        if (nowcurrency != 'TWD') {
            $("#calc_cost").html("預計收入 : " + (select_stock_price * $("#inp_count").val()).toFixed(2) + "元");
            $('#calc_balance').html("預計餘額 : " + (mybalance + (select_stock_price * $("#inp_count").val()).toFixed(2)).toFixed(2) + "元");
            $('#calc_balance').removeClass('text-danger');
            $("#btn_buy").attr("disabled", false);
        }
        else {
            $("#calc_cost").html("預計收入 : " + (select_stock_price * $("#inp_count").val()).toFixed(2) * 1000 + "元");
            $('#calc_balance').html("預計餘額 : " + (mybalance + (select_stock_price * $("#inp_count").val()).toFixed(2) * 1000).toFixed(2) + "元");
            $('#calc_balance').removeClass('text-danger');
            $("#btn_buy").attr("disabled", false);
        }

    }
});

$("#mybalance").html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 目前錢包餘額')
$.ajax({
    url: "/stockPassbook",
    type: "POST",

    success: function (data) {
        console.log(data.passbook[Object.keys(data.passbook)[0]].balance);
        $("#mybalance").html("目前錢包餘額 : " + data.passbook[Object.keys(data.passbook)[0]].balance + "元");
        mybalance = data.passbook[Object.keys(data.passbook)[0]].balance;
    }
})
$("#inp_count").on('change', function () {
    if (isbuy) {
        if (nowcurrency != 'TWD') {
            $("#calc_cost").html("預計花費 : " + (select_stock_price * $("#inp_count").val()).toFixed(2) + "元");
            $('#calc_balance').html("預計餘額 : " + (mybalance - (select_stock_price * $("#inp_count").val()).toFixed(2)).toFixed(2) + "元");
            if (mybalance - (select_stock_price * $("#inp_count").val()).toFixed(2) < 0) {
                $('#calc_balance').addClass('text-danger');
                $("#btn_buy").attr("disabled", true);
            } else {
                $('#calc_balance').removeClass('text-danger');
                $("#btn_buy").attr("disabled", false);
            }
        } else {
            $("#calc_cost").html("預計花費 : " + (select_stock_price * $("#inp_count").val()).toFixed(2) * 1000 + "元");
            $('#calc_balance').html("預計餘額 : " + (mybalance - (select_stock_price * $("#inp_count").val()).toFixed(2) * 1000).toFixed(2) + "元");
            if (mybalance - (select_stock_price * $("#inp_count").val()).toFixed(2) * 1000 < 0) {
                $('#calc_balance').addClass('text-danger');
                $("#btn_buy").attr("disabled", true);
            } else {
                $('#calc_balance').removeClass('text-danger');
                $("#btn_buy").attr("disabled", false);
            }
        }
    }
    else {
        if (nowcurrency != 'TWD') {
            $("#calc_cost").html("預計收入 : " + (select_stock_price * $("#inp_count").val()).toFixed(2) + "元");
            $('#calc_balance').html("預計餘額 : " + (mybalance + (select_stock_price * $("#inp_count").val()).toFixed(2)).toFixed(2) + "元");
            $('#calc_balance').removeClass('text-danger');
            $("#btn_buy").attr("disabled", false);
        }
        else {
            $("#calc_cost").html("預計收入 : " + (select_stock_price * $("#inp_count").val()).toFixed(2) * 1000 + "元");
            $('#calc_balance').html("預計餘額 : " + (mybalance + (select_stock_price * $("#inp_count").val()).toFixed(2) * 1000).toFixed(2) + "元");
            $('#calc_balance').removeClass('text-danger');
            $("#btn_buy").attr("disabled", false);
        }

    }
})

function refush_inv() {
    $('#inv_table').html('');
    $("#btn_ref_inv").html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 重新整理')
    $("#btn_ref_inv").attr("disabled", true);
    $.ajax({
        url: "/stock/inventory_list",
        type: "POST",
        success: function (data) {

            $("#btn_ref_inv").html('重新整理庫存')
            $("#btn_ref_inv").attr("disabled", false);
            console.log(data['inventory']);
            data = data['inventory'];
            for (let i = 0; i < data.length; i++) {
                console.log(data[i]);
                data[i].stockex = data[i].stockex.replace('&*&', '.');
                // data[i].name = data[i].name.replace("(" + data[i].stockex + ")", '');
                $('#inv_table').html($('#inv_table').html() + '<tr id="trname_' + data[i].stockex + '"><td>' + data[i].stockex + '</td><td id="tdname_' + data[i].stockex + '"><span class="spinner-border spinner-border-sm" role="status"></span></td><td>' + data[i].inv_num + '</td><td>' + parseFloat(data[i].mcost).toFixed(2) + '</td><td id="tdprice_' + data[i].stockex + '">' + '<span class="spinner-border spinner-border-sm" role="status"></span>' + '</td><td id="tdpl_' + data[i].stockex + '">' + '--' + '</td><td id="tdroi_' + data[i].stockex + '">' + '--' + '</td></tr>');

            }
            //tr 開頭的都是庫存表格
            $("tr[id^='trname_']").on('click', function () {
                let stock = $(this).attr('id').replace('trname_', '');

                ssn.events.afterChange(0, defa = stock);
            })
            inventory_list = data;
            get_inv_price();
            // data['inventory'].forEach(element => {
            //     $('#inv_table').html($('#inv_table').html() + '<tr><td>' + element.stock + '</td><td>' + element.count + '</td><td>' + element.cost + '</td><td>' + element.price + '</td><td>' + element.profit + '</td></tr>');

            // });
            $("#btn_ref_inv").attr("disabled", false);
            $("#btn_ref_inv").html('重新整理')
        }
    })
}
//ajax get inventory list price and profit use queue
function get_inv_price() {
    if (inventory_list.length == 0) {
        return;
    }
    let stock = inventory_list[0].stockex;
    let count = inventory_list[0].inv_num;
    let mcost = inventory_list[0].mcost;

    $.ajax({
        url: "/stock_info",
        type: "POST",
        data: {
            stock: stock,
        },
        success: function (data) {
            console.log(data);
            let price = data.price;
            let name = data.name;
            let profit = (price - mcost) * count;
            let roi = (price - mcost) / mcost * 100;
            document.getElementById('tdname_' + stock).innerHTML = name;
            document.getElementById('tdprice_' + stock).innerHTML = price + " " + data.currency;
            document.getElementById('tdpl_' + stock).innerHTML = profit.toFixed(2);
            document.getElementById('tdroi_' + stock).innerHTML = roi.toFixed(2) + '%';


        },
        error: function (err) {
            console.log(err);
        }
    })
    inventory_list.shift();
    get_inv_price();
}

refush_inv();
btn_ref_inv.addEventListener('click', refush_inv);

$("#btn_buy").on('click', function () {
    if (isbuy) {
        $("#btn_buy").html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 買進中')
        $("#btn_buy").attr("disabled", true);
        $.ajax({
            url: "/stock/buy",
            type: "POST",
            data: {
                stock: stockCode,
                amount: $("#inp_count").val(),
                price: select_stock_price
            },
            success: function (data) {
                console.log(data);
                $("#btn_buy").html('下單')
                $("#btn_buy").attr("disabled", false);
                refush_inv();
                $("#btn_get_stock_info").attr("disabled", true);
                $("#btn_get_stock_info").html('取得現價 (等待更新)');
                ssn.events.afterChange();

            },
            error: function (err) {
                console.log(err);
            }
        })
    } else if (!isbuy) {
        $("#btn_buy").html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 賣出中')
        $("#btn_buy").attr("disabled", true);
        $.ajax({
            url: "/stock/sell",
            type: "POST",
            data: {
                stock: stockCode,
                amount: $("#inp_count").val(),
                price: select_stock_price
            },
            success: function (data) {
                console.log(data);
                $("#btn_buy").html('下單')
                $("#btn_buy").attr("disabled", false);
                refush_inv();
                $("#btn_get_stock_info").attr("disabled", true);
                $("#btn_get_stock_info").html('取得現價 (等待更新)');
                ssn.events.afterChange();

            },
            error: function (err) {
                console.log(err);
            }
        })
    }
})



$(".dropdown-menu li a").click(function () {
    var selText = $(this).text();
    $(this).parents('.btn-group').find('.dropdown-toggle').text("Intenvel " + selText);
    intenvel = selText;
    console.log("stockCode", stockCode)
    if (stockCode) {
        ssn.events.afterChange(undefined, stockCode);
    }
});

//btn_range_1d btn_range_5d ... click
$("button[id^='btn_range_']").click(function () {
    var selText = $(this).text();
    timerange = selText;
    console.log("stockCode", stockCode)
    if (stockCode) {
        ssn.events.afterChange(undefined, stockCode);
    }
});

var isResize = false;
var ishover = false;
$("#inv_hr").hover(function () {
    //mouse 改變成上下調整
    $(this).css("cursor", "ns-resize");
    ishover = true;
}, function () {
    $(this).css("cursor", "default");
    ishover = false;
});

$("#inv_hr").mousedown(function () {
    if (ishover) {
        isResize = true;
    }
});

$(document).mouseup(function () {
    isResize = false;
});

$(document).mousemove(function (e) {
    if (isResize) {
        var filahight = e.clientY - $("#inv_hr").offset().top * 0.5;
        $("#k_line_chart").css("height", filahight);
        k_line_chart.resize();


    }
});