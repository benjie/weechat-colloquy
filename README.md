Colloquy iOS / Weechat Push
===========================

Put this in `~/.weechat/python/` and then in weechat run:

    /python load python/colloquy_push.py

If you want it to auto load then change directory into
`~/.weechat/python/autoload/` and run:

    ln -s ../colloquy_push.py ./

How it works
------------

Intercepts the `PUSH` commands emitted by Colloquy (iOS) to get your push
token, then sends this to the colloquy servers on mention, as [documented
here](http://colloquy.mobi/bouncers.html).

Issues
------

Implements a 5 second socket timeout, so in the event that colloquy's servers
aren't responding fast enough you may have Weechat lock up for 5 seconds or so.

Is written by someone who doesn't really know Python, so is probably terribly
coded. (Pull requests gratefully received.)
