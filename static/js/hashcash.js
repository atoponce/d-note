function validate_token(resource) {
    //var resource = document.getElementById('hashcash').value;
    var randomstring = nonce();
    var d = new Date();
    var yyyymmdd = d.yyyymmdd();
    var pre_token = '1:16:'+yyyymmdd+':'+resource+'::'+randomstring+':';
    //var start = new Date();
    token = mint_token(pre_token);
    //var end = new Date();
    //var fin = (end-start)/1000;
    //var perf = parseInt(token.split(':')[6], 36);
    //alert(fin+' seconds\n'+perf/fin+' tokens per second\n'+token);
    alert(token);
}

function nonce() {
    var chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789/+';
    var randomstring = '';
    for (i=16; i--;) {
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
    for(;++counter;) {
        if(CryptoJS.SHA1(pre_token+counter.toString(36)).toString().substring(0,4) === '0000') { break; }
    }
    token = pre_token+counter.toString(36);
    return token;
}
