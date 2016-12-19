function hideExport() {
    var ua=window.navigator.userAgent;
    var myStyle = '';
    if(ua.indexOf('Chrome') != -1){myStyle='none'}
    document.getElementById('export').style.display=myStyle;
}

