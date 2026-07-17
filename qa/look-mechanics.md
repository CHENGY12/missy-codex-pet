# Missy look mechanics

Missy is a round-bodied calico cat with a stable four-paw stance. Her gaze is led by the complete yellow-green eye globes, followed by a restrained rigid head yaw or pitch, small eyelid changes, muzzle and pink-nose movement, and subtle ear and upper-chest follow-through. Her paws, belly, lower torso, baseline, practical sprite scale, and volume stay anchored. The thick black-and-orange tail remains attached and nearly stable, with only a small continuous lag.

Preserve Missy's real asymmetry in every direction: the dark eye patch, black ear, warm orange crown area, mostly white coat, distinct orange flank oval, smaller back patches, and thick black tail with orange bands remain body-attached and must not flip as if the whole sprite were mirrored. Her original eye construction stays intact: chartreuse/yellow-green irises, dark pupils, rims, highlights, and eyelids rotate or redraw together. Never add eye whites, googly eyes, detached pupils, or a second eye layer.

## Cardinal pose families

- `000 up`: both eye surfaces aim upward; eyelids open toward the top, muzzle and pink nose lift slightly, and the head pitches up while both large ears remain readable. The torso and paws do not rise.
- `090 screen-right`: the head and muzzle yaw toward the viewer's right. Nose tip and pupils sit unmistakably right of head center; more of the screen-left cheek and crown is visible, while the far screen-right cheek and eye are slightly occluded. Markings stay attached to their anatomical sides.
- `180 down`: both eye surfaces aim downward, upper eyelids lower slightly, the chin tucks toward the white chest, and the head pitches forward without squashing the face. Ears remain upright and the four-paw base stays fixed.
- `270 screen-left`: the head and muzzle yaw toward the viewer's left. Nose tip and pupils sit unmistakably left of head center; more of the screen-right cheek and crown is visible, while the far screen-left cheek and eye are slightly occluded. Markings stay attached to their anatomical sides.

## Motion budget and continuity

Each 22.5-degree step moves the eyes first and the head, muzzle, eyelids, ears, upper chest, and tail lag by one small, roughly even increment. Diagonals interpolate between adjacent cardinal families. Preserve face proportions, belly volume, paw registration, baseline, tail attachment, and pixel-art scale. `157.5 -> 180`, `337.5 -> 000`, and the row boundary must remain single-step transitions with no snap, scale pop, body slide, whole-sprite rotation, affine tilt, marking flip, or eye replacement.
