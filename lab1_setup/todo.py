from flask import Flask
from reactpy import component, html, use_state, run
from reactpy.backend.flask import configure
from cheroot import wsgi

app = Flask(__name__)

@component
def TodoApp():
    todos, set_todos = use_state([
        {"text": "PyBoy Emulator testen", "done": False, "uri": None},
        {"text": "MetaKernel Gateway prüfen", "done": True, "uri": "https://v1rtu4lyz1um.com"},
    ])
    text, set_text = use_state("")
    drop_text, set_drop_text = use_state("")

    def add_todo(event):
        event.prevent_default()
        if not text.strip():
            return
        set_todos([*todos, {"text": text, "done": False, "uri": None}])
        set_text("")

    def archive(event):
        event.prevent_default()
        set_todos([t for t in todos if not t.done])

    remaining = sum(1 for t in todos if not t.done)

    return html.div(
        {"style": {"font_family": "sans-serif", "padding": "20px"}},
        html.h2("SystemTUV Test Lab (ReactPy Edition)"),
        html.div(
            html.span(f"{remaining} of {len(todos)} remaining"),
            " [ ",
            html.a({"href": "#", "on_click": archive}, "archive"),
            " ]",
            html.ul(
                {"style": {"list_style_type": "none", "padding": 0}},
                [
                    html.li(
                        {"key": i},
                        html.input({
                            "type": "checkbox",
                            "checked": todo["done"],
                            "on_change": lambda e, idx=i: set_todos([
                                {**t, "done": not t["done"]} if j == idx else t
                                for j, t in enumerate(todos)
                            ]),
                        }),
                        html.span(
                            {"style": {"text_decoration": "line-through" if todo["done"] else "none"}},
                            todo["text"],
                        ),
                        (
                            html.a(
                                {
                                    "href": "#",
                                    "on_click": lambda e, u=todo["uri"]: set_drop_text(f"Opening URI: {u}"),
                                },
                                " (view url)",
                            )
                            if todo["uri"]
                            else None
                        ),
                    )
                    for i, todo in enumerate(todos)
                ],
            ),
            html.form(
                {"on_submit": add_todo},
                html.input({
                    "type": "text",
                    "value": text,
                    "on_change": lambda e: set_text(e["target"]["value"]),
                    "placeholder": "add new todo here",
                    "size": 30,
                }),
                html.input({"type": "submit", "value": "add", "style": {"margin_left": "5px"}}),
            ),
            html.div({"style": {"margin_top": "10px", "color": "#666"}}, drop_text),
        ),
    )

# ReactPy an Flask anbinden
configure(app, TodoApp)

if __name__ == "__main__":
    print("[SystemTUV] Starte Cheroot WSGI Server für ReactPy Test Lab...")
    server = wsgi.Server(
        bind_addr=("0.0.0.0", 8080),
        wsgi_app=app
    )
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
