# kicad-pcb-text

Formats the refs and values on their own layers and the way I want.

 0. Install plugin, if not done already.

 1. Create a layer called `Refs` and with colour `#00ff20ff`.

 2. Create a layer called `Values` and with colour `#00d6ffff`.

 3. Run plugin.


# Weekly rant about Python

There's no configuration dialog to edit the formatting rules, because I can't be
arsed wasting time fighting with the disappointing mess that is text-format
(e.g. YAML/JSON/XML) serialisation in Python, combined with 3rd-party dependency
issues relating to how Kicad provides its own Python environment.

C# in 2010 was far better at it than Python is in 2022...
Hell, even Java beats Python in this area.
