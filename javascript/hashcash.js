function validate_token() {
    var resource = document.getElementById('hashcash').value;
    var randomstring = nonce();
    var d = new Date();
    var yyyymmdd = d.yyyymmdd();
    var pre_token = '1:12:'+yyyymmdd+':'+resource+'::'+randomstring+':';

    //var start = new Date();
    token = mint_token(pre_token);
    //var end = new Date();
    //var fin = (end-start)/1000;

    //var perf = token.split(':')[6];
    //alert(fin+' seconds\n'+perf/fin+' tokens per second');
}

function nonce() {
    var chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789/+';
    var string_length = 16;
    var randomstring = '';

    for (var i=0; i<string_length; i++) {
        var rnum = Math.floor(Math.random() * chars.length);
        randomstring += chars.substring(rnum,rnum+1);
    }

    return randomstring;
}

Date.prototype.yyyymmdd = function() {
    var yyyy = this.getFullYear().toString();
    var mm = (this.getMonth()+1).toString(); // getMonth() is zero-based
    var dd  = this.getDate().toString();

    return yyyy + (mm[1]?mm:"0"+mm[0]) + (dd[1]?dd:"0"+dd[0]); // padding
};

function mint_token(pre_token) {
    var counter = 0;

    while(true){
        if(CryptoJS.SHA1(pre_token+counter).toString().substring(0,3) === '000') { break; }
        counter += 1;
    }

    token = pre_token+counter;
    hash = CryptoJS.SHA1(pre_token+counter);
    return token;
}
