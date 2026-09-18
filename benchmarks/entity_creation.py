"""Native entity creation benchmark.

This intentionally measures the Python -> native boundary separately from
rendering. Rendering benchmarks will be added once the first GPU backend lands.
"""

from time import perf_counter
from paralox3d import Engine


COUNT = 100_000

engine = Engine(width=1, height=1)

start = perf_counter()
handles = [engine._create_entity() for _ in range(COUNT)]
elapsed = perf_counter() - start

print(f"Created {len(handles):,} native entities in {elapsed:.3f}s")
print(f"Rate: {len(handles) / elapsed:,.0f} entities/s")
