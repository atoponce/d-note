function make_key() {
    var text = "";
    var possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    for(i=24; i--;) {
        text += possible.charAt(Math.floor(Math.random() * possible.length));
    }
    return text;
}

function validate_form() {
    if(document.getElementById('paste').value == "") {
        alert("You need to enter a message.");
        return false;
    }
    else {
        validate_token(fingerprint);
        return true;
    }
}
