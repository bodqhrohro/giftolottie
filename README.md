Usage
=====

```
python3 read.py input.gif output.tgs
```

Installation
============

Requires `gifsicle`.

Python dependencies can be installed with:

```
pip3 install -r requirements.txt
```

Notes
=====

This is an early prototype. It's already able to successfully convert simple animations, though even tiny ones rarely fit the Telegram limitations (64 kiB for gzipped and 1 MB for ungzipped data). Fortunately, there is still a big room for compression improvements and for optional vectorization.

Also, you can already use this for other Lottie-enabled applications, regardless of Telegram limits (if you really have some reason to use Lottie instead of GIFs).

The solution is completely independent from After Effects. The Lottie encoder is built from scratch by investigating the JSON schema in lottie-web and a bit of reverse engineering. The GIFs are read with a slightly modified [gif2numpy](https://github.com/bunkahle/gif2numpy) library.
