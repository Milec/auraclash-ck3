# Potential trait artwork

Three transparent PNG masters, generated with the built-in image_gen tool using the existing AuraClash trait art as a reference. The full prompts are preserved in `prompts.json`.

- `mortal.png`: closed bronze spiritual seed.
- `earthly.png`: opening jade seed and golden center.
- `heavenly.png`: ivory lotus and luminous pearl.
- `preview.png`: labelled artwork with the native 120px versions below.

`python tools/build_trait_icons.py` builds the three native DDS textures. The trait chooses the highest revealed tier across Limit and Talent; each track's exact grade remains separate in its tooltip. Transparent margins and cloth-backed diamond frames follow the existing trait set.
