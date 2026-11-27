"""Export every dashboard chart as PNG into ./figures (needs kaleido + Google Chrome installed)."""
import pandas as pd, dashboard as d
df = d.DF
figs = d.build_figures(df, "revenue", "W", df.date.min(), df.date.max())
figs.pop("_meta")
for i, (name, fig) in enumerate(figs.items(), 1):
    fig.write_image(f"figures/fig{i}_{name}.png", width=1200, height=520, scale=2); print("saved", name)
