function doExport() {
    var $tableid = $('#tabPages').find('.tab-pane.active').find('.table').attr('id');
    exportData($tableid);
}

function exportData(src) {
    var data = document.getElementById(src).outerHTML;
    window.open('data:application/vnd.ms-excel,'+encodeURIComponent(data));
}
