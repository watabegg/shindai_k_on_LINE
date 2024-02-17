function formatDate(date) { // 日付をYYYY-MM-DDに変換する関数
    var yyyy = date.getFullYear();
    var mm = String(date.getMonth() + 1).padStart(2, '0');
    var dd = String(date.getDate()).padStart(2, '0');
    return `${yyyy}-${mm}-${dd}`;
}

function parseCsv(data) {
    // csv配列を変数に格納
    var time_list = $.csv.toArrays(data);
    return time_list
}

function getTimestamp() {
    var date = new Date();
    var year = date.getFullYear();
    var month = padZero(date.getMonth() + 1);
    var day = padZero(date.getDate());
    var hours = padZero(date.getHours());
    var minutes = padZero(date.getMinutes());
    var seconds = padZero(date.getSeconds());
    return year + '-' + month + '-' + day + ' ' + hours + ':' + minutes + ':' + seconds;
}

function padZero(num) {
    return (num < 10 ? '0' : '') + num;
}