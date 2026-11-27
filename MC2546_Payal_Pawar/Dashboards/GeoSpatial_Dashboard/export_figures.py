"""Export every dashboard chart as PNG into ./figures (needs kaleido + Google Chrome installed)."""
import dashboard as d
figs = d.build_figures(d.DF, "pm25", "Bubble Map", "Delhi")
for i, (name, fig) in enumerate(figs.items(), 1):
    fig.write_image(f"figures/fig{i}_{name}.png", width=1200, height=600, scale=2); print("saved", name)
