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