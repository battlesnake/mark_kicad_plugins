# clone

Replicate-layout kept making a mess, so I wrote my own plugin to do replication
of subcicruits from hierarchical sheets in my own simpler way.

 0. Install plugin, if not done already.

 1. Select stuff to replicate.

 2. Run plugin.


# text

Formats the refs and values on their own layers and the way I want.

 0. Install plugin, if not done already.

 1. Create a layer called `Refs` and with colour `#00ff20ff`.

 2. Create a layer called `Values` and with colour `#00d6ffff`.

 3. Run plugin.


# Weekly rant about Python

There's no configuration dialog to edit the plugin config, because I can't be
arsed wasting time fighting with the disappointing mess that is text-format
(e.g. YAML/JSON/XML) serialisation in Python, combined with 3rd-party
dependency issues relating to how Kicad provides its own Python environment.
GUI development in Python is also a stone-age pain in the arse compared to the
likes of Delphi or C# 10-20 years ago.
