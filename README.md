d-note
======

Disclaimer
----------

Currently, there is no code. I can't even guarantee that there will be any
code. This is just an idea. If I get it working, and code starts showing,
great. If not, I'm sorry, but it appears that I have other things on my
plate that are taking high priority.

Introduction
------------

Self destructing notes you can run on your own web server. I got the idea
from a number of websites doing pretty much the same thing:

* https://oneshar.es/
* https://privnote.com/
* https://quickforget.com/
* https://onetimesecret.com/
* https://burnnote.com/

And many more. Unfortunately, none of the above sites seem to be interested
in benefiting the community as a whole by providing their source code, even
though there seems to be a demand for it. So, that is the goal of this
project.

The name of the project is inspired by the "H-Bomb", or hydrogen bomb. I
wanted a clever name for self destructing notes that was not in use, and
something that had a familiar ring to it. "d-note" seemed to fit for
"destructive note", and as already mentioned, inspired by the hydrogen
bomb.

Ideas
-----

* Store each entry in the DB in 100% encrypted form.
    * Use AES with a randm key stored in the config.
* Require SSL for web clients.
* Default timer of 3 minutes after opening to destruction.
* Default timer of 24 hours after creating to destruction.
* Scrub table entry before deletion.
* Use MyISAM instead of InnoDB to prevent journaling.
    * SQLite? MySQL? PostgreSQL? Others?
* Require encrypted filesystem underneath DB?
* Force browsers to not cache the site.
* JavaScript option to prevent copying.
* "Spotlight" option to make screenshots ineffective.
* Image generation to create copy/pastes.
    * If copied, set JavaScript timer to clear clipboard in 1 minute.
    * Randomize clipboard to discourange key logging.
