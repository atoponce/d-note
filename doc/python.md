Python Documentation
====================

URL Generation
--------------

The URLs of self destructing notes should not be predictable in any manner, and 
are generated from a 16 byte random nonce.

This nonce is passed through a key derivation function to derive 3 
additional random byte strings.  

- a 32 byte AES key
- a 64 byte HMAC-SHA512 key
- a 16 bytes random to generate a filename for incoming note.

The URL that the note can be found at is the nonce encoded 

base64.urlsafe_b64encode(nonce)[:22]

The note is encryted using AES256-CTR-HMAC-SHA512 and stored on disk, with the 
keys and filename as derived from the nonce.

If the note creator adds an additional passphrase then that passphrase is used 
to derive the AES and HMAC keys, rather than the ones from the nonce. This is 
done in the same way as from the random nonce. The passphrase is passed through
a key derivation function to generating AES265 and HMAC-512 keys.

As the filename on disk is derived from passing the nonce through a one way
function it is not possible for the server operator to link a particular
filename to the URL used to access it.

The use of an HMAC-SHA512 tag on the AES256-CTR encrypted prevents the 
server operator from being able to tamper with the contents of a note
whilst they are stored on disk.

The valid characters for our URLs are as follows:

    ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_

So, a valid URL for your self destructing notes could be:

    https://example.com/FVvA0UW6lRl-OOhM-virDU

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
