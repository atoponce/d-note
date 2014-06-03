function make_key() {
    var text = "";
    var possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    for(i=24; i--;) {
        text += possible.charAt(Math.floor(Math.random() * possible.length));
    }
    return text;
}

function please_wait() {
    span = document.getElementById('progress');
    span.style.visibility = 'visible';
}

function validate_form() {
    if(document.getElementById('paste').value == "") {
        alert("You need to enter a message.");
        return false;
    }
    else if (document.getElementById('duress').checked && document.getElementById('passphrase').value == "") {
        alert("You need to enter a passphrase if you enable a duress key");
        return false;
    }
    else {
        please_wait();
        setTimeout(function(){},0);
        validate_token(fingerprint);
        return true;
    }
}
