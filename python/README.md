Python Documentation
====================

URL Generation
--------------

URLs for self destructing notes should not be predictable in any manner.
Thus, an eight-character base64-encoded string is generated for each
submission. This will give us enough random URLs to avoid a collision with
1 in 281,474,976,710,656. The code should be self-documenting, however,
this might explain things a bit more clearly.

Each URI starts with using data found in /dev/urandom by using
`s=os.urandom(72)`. This gives the source of the URI 72-bits of entropy,
which should be sufficient for generating URLs.

We then encode the string using `base64.urlsafe_b64encode(s)[:8]`. This
gives us 8 characters for our URL. The valid characters for our URLs are
thus:

    ABCDEFGHIJKLMNOPQRSTUPVXYZabcdefghijklmnopqrstupvxyz0123456789-_

So, a valid URL for your self destructing notes could be:

    https://exmaple.com/i55GWOnH

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
