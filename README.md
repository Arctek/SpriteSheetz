# SpriteSheetz
Qt/Python tool for building tiled maps using sprites.
I didn't like the current options available to easier to whip something up on my own.

Things like:
- Grouping tiles into objects on a per sprite sheet basis
- Sub-tile hitboxes/collision, as well multi-tile
- Non-rendering placeholder objects/tiles, i.e. if we have 5 types of trees randomly drawn, I would still like to see a tree as a placeholder when designing a map and not some symbolic square
- Different insertion origins for objects/tiles, i.e. a houses should place floor up but a waterfall should place top down
- Pure fill tiles, i.e. solid color, without having to resort to using an image tile
- On a map a layer should be able to contain both objects or tiles
- Output to be JSON and not some CSV abomination with arrays packed with empty fields (or zeroes)
- Pathing, triggers and other map logic to be added later as well. Since it makes sense to put everything related to a map... on a map
