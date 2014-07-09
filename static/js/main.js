function validate_form() {
    if(document.getElementById('paste').value == "") {
        alert("You need to enter a message.");
        return false;
    }
    else {
        return true;
    }
}
