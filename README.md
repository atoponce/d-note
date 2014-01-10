d-note
======

Introduction
------------

d-note is a self destructing notes application you can run on your own web
server. I got the idea from a number of websites doing pretty much the same
thing:

* https://oneshar.es/
* https://privnote.com/
* https://quickforget.com/
* https://onetimesecret.com/
* https://burnnote.com/

And many more. Unfortunately, none of the above sites seem to be interested
in benefiting the community as a whole by providing their source code, even
though there seems to be a demand for it. Further, by using a third party
service, you have no guarantee that they are not sharing your data with
third parties. By running your own server, you know who has your data and
who doesn't.

The name of the project is inspired by the "H-Bomb", or hydrogen bomb. I
wanted a clever name for self destructing notes that was not in use, and
something that had a familiar ring to it. "d-note" seemed to fit for
"destructive note", and as already mentioned, inspired by the hydrogen
bomb.

Securing The Data
=================

Server Side
-----------

All notes are compressed using ZLIB and encrypted using Blowfish in ECB mode
before being written to disk. Never at any point is the note in plaintext on
disk.

Blowfish was chosen as the cipher for encrypting the data, as the key can be
any length, whereas AES requires static key lengths. This could be enforced
client-side with Javascript, but some clients have Javascript disabled.

ECB mode was chosen over CBC for encrypting the blocks, due to not wanting to
maintain an initialization vector. Even though ECB can leack information about
plaintext blocks, the data is compressed with ZLIB before encrypted. This
increases the entropy of the plaintext, and removes duplicated blocks from the
plaintext, as is the design of compression algorithms.

Although I cannot enforce this, you should serve the application over SSL. The
plaintext must be transmitted between the browser and the server, before it can
be encrypted. The data is also decrypted on the server, and transmitted to the
recipient's browser. As such, you should protect the data from being sniffed
using SSL on this application.

When the note is destroyed, it is first overwritten once with random data,
then removed. There are a couple of benefits from this:

* If the underlying filesystem is copy on write, then new random data is
  written to new sectors on disk, making it difficult to know precisely where
  the encrypted file ended and where the random data started.
* If the underlying filesystem is a journaled filesystem, the journal may have
  logged entries of the data. But again, because it's compressed then
  encrypted, it will be very difficult to know when the encrypted data was
  stored and when it was overwritten with random data.

Client Side
-----------

There are many things I could do to greatly discourage the recipient from
copying the plaintext, but they're mostly just annoying. There's nothing to
stop the recipient from memoring the note, taking a screenshot (or many), or
copying and pasting the text. If the recipient really wants the note saved that
badly, it will happen. As such, the only thing that can be done is destroying
the note after a given interval, to prevent it from being viewed again.

To prevent form spam, a JavaScript implementation of Hashcash is installed. The
client browser must solve a puzzle accurately before submitting the form. Upon
page load, a token is generated that uniquely identifies your browser with
about 94% accuracy using a JavaScript implementation of browser fingerprints,
as introduced by the EFF. This token is submitted to the server during form
submission. If the SHA1 hash of the token is valid, the form is sucessfully
submitted. Otherwise, an error is thrown.

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

JavaScript Documentation
========================

Hashcash
--------

The point of a Hashcash implementation is to prevent form spam. I'm not
sure what the benefit of spammers would be to use self-destructing notes,
but nonetheless, I'm not really interested in entertaining it.
Implementaning Hashcash as a proof-of-work system is simple enough to
deter most spammers.

The format of the token is as follows:

    1:16:$date:$fingerprint::$nonce:$counter

* 1: The version of the Hashcash token format.
* 16: The number of bits that should be validated.
* $date: The date the page was loaded.
* $fingerprint: A hash representing the uniqueness of your browser.
* $nonce: A randomly generated number.
* $counter: A base36 number incremented until the token is valid.

Once the token is generated, the following steps take place:

* The token is embedded invisibly into the form.
* The client submits the form with the minted token.
* Server verifies if the token is valid.
    * If valid, the form submits.
    * If not valid, the user is notified submission failed.
    * Tokens are stored server-side to prevent double-spending.

A minted Hashcash token generated by the client would then need to look
something like this:

    1:16:20140104:501550863::lefpClHgfZmo+RP+:1h7v

This is valid, because the SHA1 hash of the above token is:

    000041cf0569217ec3e5f70cbefb7994837a8afb

which starts with 16-bits of leading zeros. The work is forced on the
client, which inserts the token into the form. Even on modern hardware,
this should be computationally difficult for the client CPU, and could take
up to a second or two to create a valid token string. However, verification
of the token is computationally easy for the server to verify.

The minting of the token should be done in the background while the user is
typing the note in the form. Thus, when the submit button is pressed, no
additional waiting is needed.

More info can be found at http://hashcash.org.

The sha1.js code is copyright Jeff Mott, and the code can be found upstream at
[his Google Code page](https://code.google.com/p/crypto-js).


Browser Fingerprints
--------------------

Browser fingerprinting is unique enough to anonymously identify a browser with
94% accuracy. This is a JavaScript implementation of the [research done by the
Electronic Frontier Foundation](https://panopticlick.eff.org/). The browser is
queried for many things:

* User agent string
* Screen color depth
* Language
* Installed plugins with supported MIME types
* Timezone offset
* Local storage
* Session storage
* ... and more

Each of these values are passed through a non-cryptographic hashing function to
produce a fingerprint that represents your browser. The hash is MurmurHash3 with
a 32-bit output.

The fingerprint.js code is copyright Valentin Vasilyev, and can be found
upstream at [his Github page](https://github.com/Valve/fingerprints).
