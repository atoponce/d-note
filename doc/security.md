Securing The Data
=================

Server Side
-----------

All notes are compressed using ZLIB and encrypted using AES in CTR mode with
HMAC-SHA512 before being written to disk. Never at any point is the note in
plaintext on disk, and the keys used for AES encryption and HMAC-SHA512 tag are 
part of the URL, and also never stored on disk.

Although I cannot enforce this, you should serve the application over SSL. The
plaintext must be transmitted between the browser and the server, before it can
be encrypted. The data is also decrypted on the server, and transmitted to the
recipient&#39;s browser. As such, you should protect the data from being sniffed
using SSL on this application.

When the note is destroyed, it is first overwritten once with random data, then
removed. There are a couple of benefits from this:

* If the underlying filesystem is copy on write, then new random data is
  written to new sectors on disk, making it difficult to know precisely where
  the encrypted file ended and where the random data started.
* If the underlying filesystem is a journaled filesystem, the journal may have
  logged entries of the data. But again, because it&#39;s compressed then
  encrypted, it will be very difficult to know when the encrypted data was
  stored and when it was overwritten with random data.

Client Side
-----------

There are many things I could do to greatly discourage the recipient from
copying the plaintext, but they&#39;re mostly just annoying. There&#39;s nothing
to stop the recipient from memorizing the note, taking a screenshot (or many),
or copying and pasting the text. If the recipient really wants the note saved
that badly, it will happen. As such, the only thing that can be done is
destroying the note immediately after viewing, and redirecting or refreshing the
browser after a given interval, to prevent it from being viewed again.

To prevent form spam, a JavaScript implementation of Hashcash is installed. The
client browser must solve a puzzle accurately before submitting the form. Upon
page load, a token is generated that uniquely identifies your browser with about
94% accuracy using a JavaScript implementation of browser fingerprints, as
introduced by the EFF. This token is submitted to the server during form
submission. If the SHA1 hash of the token is valid, the form is sucessfully
submitted. Otherwise, an error is thrown.

Some Mathematics
----------------

Each URL is the result of a number picked at random from a 128-bit space, or
2^128 total URLs that could be generated. Using the birthday attack, we can
estimate how long it would take to find the probability of 50% in generating a
duplicate URL.

According to the birthday attack, we would need to generate approximately
2.3x10^19 URLs to have a probability of 50% that we have generated a duplicate
URL. If we were processing one billion URLs every second, it would take 733
years before we reached that probability. Because the URL is the base-64 encoded
cryptographic nonce that is responsible for the entire structure of the
application, it is critical that the system has enough entropy to pick a truly
random number from that 128-bit space.

For AES in counting mode, you are limited by a pre-determined counting space.
IE: the maximum number of blocks that you will allow to be encrypted. According
to NIST, the AES standardized block size is 16-bytes. d-note uses a counting
space of 128-bits, which gives us a total encryption size of:

    16 * 2^128 bytes == 2^132 bytes

However, d-note also uses a randomly chosen initial value to start the counting.
Due to a bug with AES in PyCrypto, if that counting value surpasses the maximum
value of the counting space, and wraps around to zero, the application will
crash. Instead, the application should crash only after every value in the
counting space has been evaluated, and a repeat value is used. Regardless, we
must back off a bit on the initial value space to prevent that counter from
wrapping back to zero.

As such, the initial value space is chosen at random from a 96-bit counting
space. This leaves a 32-bit counting space minimum of encryptable blocks, or:

    16 * 2^32 bytes == 2^36 bytes

A file that is 2^32 bytes in size is 4 GB. d-note should never need to encrypt
anything larger than 8 MB, which is 2^23 bytes in size. As such, we have enough
overhead to prevent the application from crashing due to running out of
counters.
