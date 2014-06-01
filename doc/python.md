Python Documentation
====================

URL Generation
--------------

URLs for self destructing notes should not be predictable in any manner. URLs
are generated using three pieces of information:

    - The first 22 characters are used for the filename.
    - The next 22 characters are used for the AES-128 key.
    - The last 26 characters are used for the HMAC-SHA1 key.

Before constructing our URL, we begin by creating a 52-byte random URI with:

    >>> uri_rand = Random.new().read(52)
    >>> base64.urlsafe_b64encode(uri_rand)
    'FVvA0UW6lRl-OOhM-virDUZibzpCGSKJ4NVf8aBbGGI9EbFgCD86fZczcw7-UXsJA4Gwmg=='

Thus, a 70-character base64-encoded string is generated for each
submission (ignoring the last two '==' characters). This will give us enough
random URLs to avoid a collision with 1 in 2^560. The code should be
self-documenting, however, this might explain things a bit more clearly.

The filename is encoded using `base64.urlsafe_b64encode(uri_rand)[:22]`. This
gives us the first 22 characters of our random URI for our filename.

The note is encrypted with AES. The encryption key is created using
`uri_rand[16:32]`. However, if the user supplies a password in the form, then
the AES encryption key is created with
`PBKDF2(passphrase,salt1.decode("hex")).read(16)`, where `salt1` is a random
static string as part of the installation. Should the encrypted note land into
the wrong hands, PBKDF greatly reduces the speed at which a brute force attack
can be mounted against the encrypted text looking for the password. This key
gives us the next 22 characters in our base64 URL.

Finally, the encrypted note is protected with message authentication using
HMAC-SHA1. This ensures data integrity, both reading the encrypted data from
disk, as well as ensuring all bits are in place on the wire. The MAC key is
created with `uri_rand[32:]` by default, unless a user supplies a form password.
If a password is supplied, then the MAC key is created with
`PBKDF2(passphrase,salt2.decode("hex")).read(20)`, for the same reasons as
above. This gives us the last 26 characters of our URL.

The valid characters for our URLs are as follows:

    ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_

So, a valid URL for your self destructing notes could be:

    https://example.com/FVvA0UW6lRl-OOhM-virDUZibzpCGSKJ4NVf8aBbGGI9EbFgCD86fZczcw7-UXsJA4Gwmg

d-note does not keep track of which URLs have been generated. Thus, it is
possible, although highly improbable, that the same URL could be generated
for two different form submissions. Of course, the application will check
against any valid notes that have not yet self destructed, but will not
check for ones that have been previously destroyed.

Thus, it is possible that a URL that has already self destructed could be
regenerated at a different time, which has not self destructed. If the
first URL is publicly accessible, that means that the second URL could be
opened by the wrong recipient accidentally. As such, these URLs should be
kept as private as possible to prevent this from happening.
