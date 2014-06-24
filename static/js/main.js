function modProd(a,b,n){
    if(b==0) return 0;
    if(b==1) return a%n;
    return (modProd(a,(b-b%10)/10,n)*10+(b%10)*a)%n;
}

function modPow(a,b,n){
    if(b==0) return 1;
    if(b==1) return a%n;
    if(b%2==0){
        var c=modPow(a,b/2,n);
        return modProd(c,c,n);
    }
    return modProd(a,modPow(a,b-1,n),n);
}

function isPrime(n){
    // Miller-Rabin primality test taken from
    // http://rosettacode.org/wiki/Miller-Rabin_primality_test#JavaScript
    if(n==2||n==3||n==5) return true;
    if(n%2==0||n%3==0||n%5==0) return false;
    if(n<25) return true;
    for(var a=[2,3,5,7,11,13,17,19],b=n-1,d,t,i,x;b%2==0;b/=2);
    for(i=0;i<a.length;i++) {
        x=modPow(a[i],b,n);
        if(x==1||x==n-1) continue;
        for(t=true,d=b;t&&d<n-1;d*=2){
              x=modProd(x,x,n); if(x==n-1) t=false;
        }
        if(t) return false;
    }
    return true;
}

function random_prime(n) {
    while(!isPrime(n)) {
        n -= 2;
    }
    return n;
}

function gcd(x, y) {
    if(!y) {
        return x;
    }
    return gcd(y, x%y);
} 

function seed() {
    var s = Math.floor(Math.random() * Math.pow(2,32));
    if(s == 0 || s == 1) {
        seed();
    }
    return s;
}

function bbs(n) {
    // Blum Blum Shub CSPRNG
    // Max int = 2^53 == (2^26)*(2^27)
    var a = new Uint32Array(n);
    var p = random_prime(2*Math.floor(Math.random() * Math.pow(2,26))-1); //odd
    var q = random_prime(2*Math.floor(Math.random() * Math.pow(2,27))-1); //odd
    var s = seed();

    // s should be coprime to p*q
    while(gcd(p*q, s) != 1) {
        s = seed();
    }

    for(i=n; i--;) {
        s = Math.pow(s,2)%(p*q);
        a[i] = s;
    }

    return a;
}

function make_key() {
    var text = "";
    var possible = 
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";
    random_array = new Uint32Array(22);

    // Prefer a cryptographically strong PRNG
    if(window.crypto && window.crypto.getRandomValues) {
        // Desktop Chrome 11.0, Firefox 21.0, Opera 15.0, Safari 3.1
        // Mobile Chrome 23, Firefox 21.0, iOS 6
        window.crypto.getRandomValues(random_array);
    }
    else if(window.msCrypto && window.msCrypto.getRandomValues) {
        // IE 11
        window.msCrypto.getRandomValues(random_array);
    }
    else {
        // Android browser, IE Mobile, Opera Mobile, other browsers
        random_array = bbs(22);
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
