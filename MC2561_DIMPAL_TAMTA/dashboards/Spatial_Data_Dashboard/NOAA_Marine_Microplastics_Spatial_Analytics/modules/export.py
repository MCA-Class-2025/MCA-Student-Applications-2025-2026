"""Download helpers."""
import io


def csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8")


def html_bytes(fig):
    return fig.to_html(include_plotlyjs="cdn").encode("utf-8")


def png_bytes(fig):
    """PNG needs the optional 'kaleido' package; returns None when unavailable."""
    try:
        return fig.to_image(format="png", scale=2)
    except Exception:
        return None


def chart_downloads(st, fig, name, key):
    c = st.columns(2)
    c[0].download_button("⬇ HTML", html_bytes(fig), f"{name}.html", "text/html", key=f"{key}_h")
    png = png_bytes(fig)
    if png:
        c[1].download_button("⬇ PNG", png, f"{name}.png", "image/png", key=f"{key}_p")
    else:
        c[1].caption("PNG needs `kaleido`")
