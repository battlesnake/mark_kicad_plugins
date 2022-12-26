# Plugin: clone

Replicate-layout is great when it works, but I often seem to have situations where the result I want isn't quite what it was intended for.

So I wrote my own plugin to do replication of subciruits from hierarchical sheets in my own way.

 0. Install plugin, if not done already.

 1. Select stuff to replicate.

 2. Run plugin.

 3. Popup appears allowing you to filter which instances of the subcircuit to replicate to, how to arrange them, etc.  Alt+click to toggle for all instances of a particular sheet.

 4. You can preview the result, and update / undo via the plugin.  You can apply the result, and have the option in the plugin to undo it via the plugin.  Do not use Kicad's own "undo" command to undo the results of the plugin, it will just make a mess.


# Plugin: text

Formats the refs and values on their own layers and the way I want.

 0. Install plugin, if not done already.

 1. Create a layer called `Refs` and with colour `#00ff20ff` (or your preference).

 2. Create a layer called `Values` and with colour `#00d6ffff` (or your preference).

 3. Run plugin.

 4. References will be put on `Refs`, values on `Values`.  Size/orientation will be reset.


# future work (subcircuits)

In future, I plan to extend the clone plugin so that it can do a bunch of other subcircuit operations too.
e.g. select a subcircuit, open plugin, filter instances of the subcircuit, then apply a transformation or arrangement strategy to the selected instances.

Long-term, I'd want to focus on template-based and pattern-based approaches to repetitive subcircuits, which could be applied across projects.
e.g. "Take this LQFT, put a 100n cap (plus vias) on every VDD/VSS pair"
