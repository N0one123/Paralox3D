# Paralox3D 0.1.1

0.1.1 expands the beginner-friendly API while keeping the low-boilerplate design of 0.1.0.

Highlights:
- richer Object transforms and hierarchy
- object lifecycle and visibility controls
- tags and object lookup helpers
- input actions and multi-key input
- native mouse position/button state and Python mouse deltas
- collision layers, triggers, and query helpers
- raycast foundation
- overlap queries and swept box/sphere query foundations
- automatic/default engine context and universal frame `dt`
- scene lifecycle and scene switching foundation
- reusable components and controller helpers
- expanded Vec3 math
- frame timers and delayed/repeating callbacks
- automatic collider sizing when an Object scale changes
- native object rotation, color, visibility, and enabled state
- large named RGB color palette
- visual feature showcase test scene
- public API cleanup

Latest 0.1.1 fixes and polish:
- fixed reactive native Object state setters
- fixed native Object rotation rendering
- fixed timer updates in the engine loop
- synchronized native mouse state before Python update callbacks
- added named color constants exported from `paralox3d`

This release is an API expansion release. Native rendering features are kept intentionally conservative while the platform layer continues to grow.
