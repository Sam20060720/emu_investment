$(function () {
    showPassbook();
    showInventory();
    $('#btnRefresh').on('click', function () { showPassbook(); });
});
var inventory = {};
// var aryChartData = [];
// var aryTableData = [];
// var aryColors = [];
var slicesAnim = {};
function showInventory(formData) {
    $.ajax({
        'type': 'GET', 'data': formData, 'url': '/stock/inventory_list',
        beforeSend: function () { $('#processing').removeClass('d-none'); },
    })
        .done(function (data) {
            inventory = data.inventory;
            console.log(inventory);
            var colors = [
                '#b91d1d', '#4169e1', '#c71585', '#008b8b', '#ff8c00',
                '#4682b4', '#ba55d3', '#ff1493', '#2e8b57', '#3b3b3b'
            ];
            var colorIndex = 0;
            var items = [];
            var row = '';
            var svalue = '';
            for (var stock in data.inventory) {
                row = data.inventory[stock];
                inventory[stock].price = 0;
                inventory[stock].value = 0;
                inventory[stock].roi = 0;
                inventory[stock].currency = row.currency;
                inventory[stock].mcost = row.mcost;
                inventory[stock].inv_num = row.inv_num;
                inventory[stock].stockex = row.stockex;
                inventory[stock].color = colors[colorIndex];

                colorIndex++;
                if (colorIndex == colors.length) {
                    colorIndex = 0;
                }

            }
            console.log(inventory);


            for (var stock in inventory) {
                row = inventory[stock];
                items.push(`
            <tr data='${row.stockex}' id='tr_${row.stockex}'>
                <td><span style="color:${row.color};">●</td>
                <td>${row.stockex}</td>
                <td id='value_${row.stockex}'>--萬 ${row.currency}</td>
                <td id='roi_${row.stockex}'>--</td>
                <td id='currconv_${row.stockex}'>--</td>
            </tr>`);
                slicesAnim[stock] = { offset: 0 };
            }

            $('#tableAssets tbody').html(items.join(''));
            drawPieChart();
            if (inventory.length == 0) {
                toastr.info('目前沒有任何資產');
            }
            else {
                $('#assets-stat').fadeIn(2000);
            }
            $('#assets-stat').fadeIn(2000);
            postBody();
            get_inv_price();

        })
        .fail(function (jqXHR) { alertError(jqXHR.status); })
        .always(function () { $('#processing').addClass('d-none'); });
}

function drawPieChart() {
    // // 圓餅圖
    google.charts.load('current', { 'packages': ['corechart'] });
    google.charts.setOnLoadCallback(drawChart);
    function drawChart() {
        var aryChartData = [];
        var aryColors = [];
        // var slicesAnim = {};
        aryChartData.unshift(['公司', '佔比']);
        for (var stock in inventory) {
            row = inventory[stock];
            svalue = parseInt(row.value) / 10.0;
            aryChartData.push([row.stockex, svalue]);
            aryColors.push(row.color);
            // slicesAnim[stock] = { offset: 0 };
        }
        var data = google.visualization.arrayToDataTable(aryChartData);
        var options = {
            title: '資產總覽',
            colors: aryColors,
            legend: { position: 'top', textStyle: { color: 'black', fontSize: 14 } },
            tooltip: { textStyle: { color: 'gray', fontSize: 16 }, showColorCode: true },
            slices: slicesAnim
        };
        var chart = new google.visualization.PieChart(document.getElementById('piechart'));
        chart.draw(data, options);

    }


}

var arrMouseon = [];

function postBody() {
    var trs = $('#tableAssets').find('tbody tr').children();
    for (var i = 0; i < trs.length; i++) {
        $(trs[i]).mouseover(function (e) {
            tdtarget = $(e.currentTarget);
            selex = tdtarget.parent();
            selexid = selex.attr('data');

            idoffset = selexid;
            if (arrMouseon.indexOf(idoffset) == -1) {
                arrMouseon.push(idoffset);
            }
        });
        $(trs[i]).mouseout(function (e) {
            tdtarget = $(e.currentTarget);
            selex = tdtarget.parent();
            selexid = selex.attr('data');

            idoffset = selexid;
            if (arrMouseon.indexOf(idoffset) != -1) {
                arrMouseon.splice(arrMouseon.indexOf(idoffset), 1);
            }

        });
    };
};

setInterval(() => {
    for (var i = 0; i < inventory.length; i++) {
        if (arrMouseon.indexOf(inventory[i].stockex) == -1) {
            if (slicesAnim[i].offset > 0) {
                slicesAnim[i].offset -= 0.02;
            }
        }
        else {
            if (slicesAnim[i].offset < 0.2) {
                slicesAnim[i].offset += 0.02;
            }
        }
    }
    drawPieChart();
    // console.log(slicesAnim);
}, 20);

//get value and roi ajax
var nowgetinv = 0;
function get_inv_price() {
    if (nowgetinv == inventory.length) {
        return;
    }
    let stock = inventory[nowgetinv].stockex;
    let mcost = inventory[nowgetinv].mcost;
    let currency = inventory[nowgetinv].currency;
    let inv_num = inventory[nowgetinv].inv_num;


    $.ajax({
        url: "/stock_info",
        type: "POST",
        data: {
            stock: stock,
        },
        success: function (data) {
            let price = parseFloat(data.price);
            console.log(price);
            let roi = ((price - mcost) / mcost * 100).toFixed(2);
            let value = (price * parseInt(inventory[nowgetinv].inv_num)).toFixed(2);
            console.log(value);
            document.getElementById('value_' + stock).innerHTML = value + ' ' + data.currency;
            document.getElementById('roi_' + stock).innerHTML = roi + '%';

            if (data.currency != "TWD") {
                $.ajax({
                    url: "/getrate",
                    type: "POST",
                    data: {
                        fromex: data.currency,
                        toex: "TWD",
                        price: value,
                    },
                    success: function (data) {
                        bnowinv = nowgetinv;
                        value = data.price.toFixed(3);
                        document.getElementById('currconv_' + stock).innerHTML = value + ' TWD';
                        // inventory[bnowinv].value = value;
                        inventory[nowgetinv].value = value;
                        drawPieChart();
                        nowgetinv++;
                        get_inv_price();
                    }
                })
            } else {
                inventory[nowgetinv].value = value;
                inventory[nowgetinv].price = price;
                inventory[nowgetinv].roi = roi;
                drawPieChart();
                nowgetinv++;
                get_inv_price();
            }

        },
    })




}

function showPassbook(formData) {
    $.ajax({
        'type': 'GET', 'data': formData, 'url': '/stockPassbook',
        beforeSend: function () { $('#btnRefresh > span').removeClass('d-none'); },
    })
        .done(function (data) {
            var items = [];
            var row = '';

            for (var key in data.passbook) {
                console.log(key)
                row = data.passbook[key];
                items.push(`
            <tr>
                <td>${row.date}</td>
                <td>${row.memo}</td>
                <td>${currency(row.withdrawal)}</td>
                <td>${currency(row.deposit)}</td>
                <td>${currency(row.balance)}</td>
                <td>${row.remarks}</td>
            </tr>`);
            }
            $('#tablePassbook tbody').html(items.join(''));
        })
        .fail(function (jqXHR) { alertError(jqXHR.status); })
        .always(function () { $('#btnRefresh > span').addClass('d-none'); });
}