function validate_token() {
    var resource = document.getElementById('hashcash').value;
    var randomstring = nonce();
    var d = new Date();
    var yyyymmdd = d.yyyymmdd();
    var pre_token = '1:20:'+yyyymmdd+':'+resource+'::'+randomstring+':';

    mint_token(pre_token);
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
    var counter = 1;
    var re = /^00000/;

    while(true){
        if(re.test(CryptoJS.SHA1(pre_token+counter))) { break; }
        counter += 1;
    }

    token = pre_token+counter;
    hash = CryptoJS.SHA1(pre_token+counter);

    alert(token + "\n" + hash);
}
