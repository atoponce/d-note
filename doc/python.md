Python Documentation
====================

URL Generation
--------------

URLs for self destructing notes should not be predictable in any manner.
Thus, a 22-character base64-encoded string is generated for each
submission. This will give us enough random URLs to avoid a collision with
1 in 2^128. The code should be self-documenting, however, this might
explain things a bit more clearly.

Each URI is built using a random string of data from the Python Crypto library,
built from a 128-bit, or 16-byte number. The URL is then base64 encoded, with
URL-safe characters.

We then encode the string using `base64.urlsafe_b64encode(u.bytes)[:22]`
from the base64 module. This gives us 22 characters for our URL. The valid
characters for our URLs are thus:

    ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_

So, a valid URL for your self destructing notes could be:

    https://example.com/cWQI4m3fRcW8zM_Mdeg3uQ

There are some notes to consider with this URL scheme:

Its format is XXXXXXXXXXXXXXXXXXXXXO, where 'O' is either AgQw.

Regardless, the server would need to be processing approximately 700
million URLs every second for 1,000 years before we reached the probability
of 1/2 for generating a duplicate URL. See the [Birthday
Attack](https://en.wikipedia.org/wiki/Birthday_attack) for more
information.

d-note does not keep track of which URLs have been generated. Thus, it is
possible, although highly improbable, that the same URL could be generated
for two different form submissions. Of course, the application will check
against any valid notes that have not yet self destructed, but will not
check for ones that have.

Thus, it is possible that a URL that has already self destructed could be
regenerated at a different time, which has not self destructed. If the
first URL is publicly accessible, that means that the second URL could be
opened by the wrong recipient accidentally. As such, these URLs should be
kept as private as possible to prevent this from happening.
