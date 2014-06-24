function bbs(n) {
    // Blum Bluh Shub CSPRNG
    var p = 3181331; // prime
    var q = 943756159; // prime
    var x = Math.floor(Math.random() * Math.pow(2,32)); // seed
    var a = new Uint32Array(n);

    // I'm not confident this will work. Untested.
    for(i=n; i--;} {
        if (x%(p*q) == 1 && (x != 0 || x != 1)) {
            a[a.length] = Math.pow(x,2)%(p*q);
        } else {
            bbs();
        }
    }

    return a;
}

function make_key() {
    var text = "";
    var possible = 
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";
    random_array = new Uint32Array(22);

    // Make some attempt at preferring a strong CSPRNG first
    if (window.crypto && window.crypto.getRandomValues) {
        // Desktop Chrome 11.0, Firefox 21.0, Opera 15.0, Safari 3.1
        // Mobile Chrome 23, Firefox 21.0, iOS 6
        window.crypto.getRandomValues(random_array);
    }
    else if (window.msCrypto && window.msCrypto.getRandomValues) {
        // IE 11
        window.msCrypto.getRandomValues(random_array);
    }
    else {
        // Android browser, IE Mobile, Opera Mobile, older desktop browsers
        for(i=22; i--;) {
            random_array[i] = Math.floor(Math.random() * Math.pow(2, 32));
        }

    }

    for(i=22; i--;) {
        text += possible.charAt(Math.floor(random_array[i] % possible.length));
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
    else {
        please_wait();
        setTimeout(function(){},0);
        validate_token(fingerprint);
        return true;
    }
}
