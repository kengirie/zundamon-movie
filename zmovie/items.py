"""画面要素の定義（ただの dict を返すヘルパー）。描画は render.py が担当する。"""


def _base(kind, **kw):
    d = dict(kind=kind, se=kw.pop("se", "tick"), jump=kw.pop("jump", False),
             delay=kw.pop("delay", 0.0), anim=kw.pop("anim", "fade_up"))
    d.update(kw)
    return d


def T(text, y, size=60, align="center", x=None, bold=False, color="w", **kw):
    """リッチテキスト。[y]黄[/] のようなマークアップ可。\\n で改行。"""
    return _base("text", text=text, y=y, size=size, align=align, x=x, bold=bold,
                 color=color, **kw)


def Card(lines, y, h, size=56, border="w", icon=None, **kw):
    """角丸の箱に入った文字。icon: None / "key" / "check"。"""
    return _base("card", lines=lines, y=y, h=h, size=size, border=border, icon=icon, **kw)


def Counter(n, y, size=150, prefix="", suffix="", color="p", comma=False, **kw):
    """0 から n まで数え上げる数字。comma=True で 3 桁区切り。"""
    kw.setdefault("anim", "pop")
    return _base("counter", n=n, y=y, size=size, prefix=prefix, suffix=suffix,
                 color=color, comma=comma, **kw)


def Strike(text, y, size=80, x=100, **kw):
    """グレーの文字に赤い取り消し線が引かれる。"""
    kw.setdefault("se", None)
    return _base("strike", text=text, y=y, size=size, x=x, **kw)


def Fig(name, stage, y, h, **kw):
    """カスタム図。同じ name の図は後の stage で置き換わる。"""
    kw.setdefault("se", "tick")
    return _base("fig", name=name, stage=stage, y=y, h=h, **kw)
