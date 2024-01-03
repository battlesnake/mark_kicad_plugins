Clone placement
===============

Clones instances of subcircuits based on hierarchical sheets in schematic.

Select as the template / source:
 - one or more footprints
 - zero or more tracks/vias/zones/zones

The plugin's config UI will let you choose which other instances of that
subcircuit you wish to apply the template to.

It looks at all schematic unit(s) of all the footprint(s) in the template, and
identifies the nearest (i.e. deepest) ancestor sheet instance to them from the
schematic sheet hierarchy tree.

Then it looks for other instances (targets) of that ancestor sheet, and uses
the footprints of the symbol instances in the targets which correspond to
symbol instances from the template's footprints, and clones a subcircuit around
them.

You can tell it to use the other instances of a specific footprint from the
template as the "anchors" to generate the subcircuit layout around, or to
re-arrange the cloned subcicruits in a grid, relative to the template
subcircuit.
