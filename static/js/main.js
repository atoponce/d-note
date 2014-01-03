function make_key() {
    var text = "";
    var possible =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789`~!@#$%^&*(){}[]/=\\?+|-_;:\',.\",."

    for(var i=0; i<24; i++)
        text += possible.charAt(Math.floor(Math.random() * possible.length));
    return text;
}
