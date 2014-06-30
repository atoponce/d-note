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
