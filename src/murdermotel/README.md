# murder motel
- http://www.catracing.org/hendrb/forum/viewtopic.php?f=33&t=27506&fbclid=IwAR3_WxH2aPG3fpleW2HkDbRDyCLU8neU7_fRPagosaQvgUGhKkGS2nnvyww
- a port to bbsengine of Murder Motel available for Image BBS 3.0
    * rem 20jan1988 little john
    * rem image 3.0 09jun2021 rug rat
- data statements
  data"wading in smelly water",135,129,  0,  0,  0,  0
       ^  description          ^   ^     ^   ^   ^   ^
                               E   N     W   S   U   D
- "smelly water" is #134, east: 135; north: 129
- "glowing sphere" - special room
  data"inside a glowing sphere",150,150,150,150,150,150
- [x] use 'with' to display credits file @since 20220613 @see https://stackoverflow.com/a/48124263
- [Text Analysis & Paragraph Detection](https://www.mobileread.com/forums/showthread.php?t=56489)
- 5 items, only 2 can be defenses. weapons are two pieces each
- 64list.exe has been very helpful @since 20220915 @see https://www.c64-wiki.com/wiki/C64list @ty ryan
- [x] load and save player data @done 20220921
- [ ] thief - special living
- [ ] wolf - special living
- [ ] booby-trap - special item
- [ ] not allowed to pick up more than 2 defenses (@since 20221003)
- [ ] when encountering wolf, only allow attack if there is a complete weapon in inventory (@since 20221005)
- [ ] if thief has a proper defense, block an attack (@since 20221005)
- [ ] when showing player items, condense complete weapons but internally keep track of each component (@since 20221008)
- [ ] properly handle KEY_F1 (help) (@since 20221008)
- [ ] during encounter w rabid wolf, output what direction the player ran in (@since 20221016)
