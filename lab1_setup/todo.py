import os
import json
import subprocess
from flask import Flask
from flask_appbuilder import AppBuilder, SQLA, BaseView, ModelView, expose
from flask_appbuilder.models.sqla import Model
from flask_appbuilder.models.sqla.interface import SQLAInterface
from sqlalchemy import Column, Integer, String, Boolean
from reactpy import component, html, use_state
from reactpy.backend.flask import configure
from cheroot import wsgi

# --- 1. Flask & FAB Initialisierung ---
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config["SECRET_KEY"] = "area51-systemtuv-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "systemtuv_lab.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLA(app)
appbuilder = AppBuilder(app, db.session)


# --- 2. UML2ORM Datenbank-Modell für Todos & Subsystem-Knoten ---
class LabTodo(Model):
    __tablename__ = "lab_todos"
    id = Column(Integer, primary_key=True)
    text = Column(String(256), nullable=False)
    done = Column(Boolean, default=False)
    uri = Column(String(512), nullable=True)
    subsystem = Column(String(64), default="mcp-context-forge")  # PyBoy, LLVM, Chromium, MCP

    def to_mcp_context(self) -> dict:
        return {
            "id": self.id,
            "task": self.text,
            "done": self.done,
            "uri": self.uri,
            "target_repo": self.subsystem,
        }


# --- 3. Subsystem-Hooks (PyBoy, LLVM, ungoogled-chromium, MCP) ---
class SubsystemBridge:
    @staticmethod
    def dispatch(subsystem: str, payload: dict) -> str:
        if subsystem == "PyBoy":
            # Konzeptioneller Hook für Headless PyBoy Tick / State-Dump
            return f"[PyBoy] Frame-Step & Memory-Hook ausgelöst für: {payload['task']}"
        elif subsystem == "llvm-project":
            # Hook für LLVM-IR / Clang / WASM-Target-Check
            return f"[LLVM-Project] IR-Pass & Target-Pipeline getriggert: {payload['task']}"
        elif subsystem == "ungoogled-chromium":
            # Isolierter Kiosk/Sandbox-Start ohne Google-Telemetrie
            return f"[ungoogled-chromium] Isolierte Sandbox-Instanz bereit für URI: {payload.get('uri') or 'about:blank'}"
        else:
            # Standard: mcp-context-forge JSON-Context-Reflektion
            return f"[mcp-context-forge] Kontext geschmiedet: {json.dumps(payload)}"


# --- 4. Reaktive ReactPy-Komponente (kompatibel mit reactpy-jupyter) ---
@component
def TodoApp():
    # Initiale Synchronisation aus der SQLAlchemy-Datenbank
    def load_from_db():
        items = db.session.query(LabTodo).all()
        if not items:
            seed = [
                LabTodo(text="PyBoy Emulator testen", done=False, uri=None, subsystem="PyBoy"),
                LabTodo(text="MetaKernel Gateway prüfen", done=True, uri="https://v1rtu4lyz1um.com", subsystem="mcp-context-forge"),
                LabTodo(text="LLVM WASM Pass verifizieren", done=False, uri=None, subsystem="llvm-project"),
                LabTodo(text="Chromium Sandbox Kiosk starten", done=False, uri="http://127.0.0.1:8080/lab/", subsystem="ungoogled-chromium"),
            ]
            db.session.add_all(seed)
            db.session.commit()
            items = seed
        return [
            {"id": i.id, "text": i.text, "done": i.done, "uri": i.uri, "subsystem": i.subsystem}
            for i in items
        ]

    todos, set_todos = use_state(load_from_db)
    text, set_text = use_state("")
    subsystem, set_subsystem = use_state("mcp-context-forge")
    drop_text, set_drop_text = use_state("SystemTUV Runtime bereit.")

    def add_todo(event):
        event.prevent_default()
        if not text.strip():
            return
        new_item = LabTodo(text=text.strip(), done=False, uri=None, subsystem=subsystem)
        db.session.add(new_item)
        db.session.commit()
        set_todos(load_from_db())
        set_drop_text(SubsystemBridge.dispatch(subsystem, new_item.to_mcp_context()))
        set_text("")

    def toggle_todo(todo_id: int):
        item = db.session.query(LabTodo).get(todo_id)
        if item:
            item.done = not item.done
            db.session.commit()
            set_todos(load_from_db())
            set_drop_text(SubsystemBridge.dispatch(item.subsystem, item.to_mcp_context()))

    def archive(event):
        event.prevent_default()
        db.session.query(LabTodo).filter_by(done=True).delete()
        db.session.commit()
        set_todos(load_from_db())
        set_drop_text("[UML2ORM] Erledigte Knoten aus SQLite-Registry archiviert.")

    remaining = sum(1 for t in todos if not t["done"])

    return html.div(
        {"style": {"font_family": "monospace", "padding": "20px", "background": "#0b0f19", "color": "#00ffcc", "border_radius": "6px"}},
        html.h2("SystemTUV Test Lab (FAB + ReactPy + MCP Edition)"),
        html.div(
            html.span(f"{remaining} of {len(todos)} remaining"),
            " [ ",
            html.a({"href": "#", "on_click": archive, "style": {"color": "#ff5577"}}, "archive"),
            " ]",
            html.ul(
                {"style": {"list_style_type": "none", "padding": "10px 0"}},
                [
                    html.li(
                        {"key": todo["id"], "style": {"margin_bottom": "8px"}},
                        html.input({
                            "type": "checkbox",
                            "checked": todo["done"],
                            "on_change": lambda e, tid=todo["id"]: toggle_todo(tid),
                        }),
                        html.span(
                            {
                                "style": {
                                    "text_decoration": "line-through" if todo["done"] else "none",
                                    "margin_left": "8px",
                                }
                            },
                            f"[{todo['subsystem']}] {todo['text']}",
                        ),
                        (
                            html.a(
                                {
                                    "href": "#",
                                    "style": {"color": "#66d9ef", "margin_left": "8px"},
                                    "on_click": lambda e, t=todo: set_drop_text(
                                        SubsystemBridge.dispatch(t["subsystem"], t)
                                    ),
                                },
                                "(dispatch / view url)",
                            )
                            if todo["uri"]
                            else None
                        ),
                    )
                    for todo in todos
                ],
            ),
            html.form(
                {"on_submit": add_todo, "style": {"margin_top": "12px"}},
                html.select(
                    {
                        "value": subsystem,
                        "on_change": lambda e: set_subsystem(e["target"]["value"]),
                        "style": {"background": "#05070a", "color": "#00ffcc", "border": "1px solid #00ffcc", "padding": "5px", "margin_right": "6px"},
                    },
                    html.option({"value": "mcp-context-forge"}, "mcp-context-forge"),
                    html.option({"value": "PyBoy"}, "PyBoy"),
                    html.option({"value": "llvm-project"}, "llvm-project"),
                    html.option({"value": "ungoogled-chromium"}, "ungoogled-chromium"),
                ),
                html.input({
                    "type": "text",
                    "value": text,
                    "on_change": lambda e: set_text(e["target"]["value"]),
                    "placeholder": "add new lab task...",
                    "size": 30,
                    "style": {"background": "#05070a", "color": "#00ffcc", "border": "1px solid #00ffcc", "padding": "5px"},
                }),
                html.input({
                    "type": "submit",
                    "value": "add",
                    "style": {"margin_left": "6px", "background": "#00ffcc", "color": "#000", "border": "none", "padding": "6px 12px", "cursor": "pointer"},
                }),
            ),
            html.pre(
                {"style": {"margin_top": "15px", "padding": "10px", "background": "#000", "border": "1px solid #00ffcc", "color": "#fff"}},
                drop_text,
            ),
        ),
    )


# --- 5. Flask-AppBuilder Views (CRUD + ReactPy Lab View) ---
class LabTodoModelView(ModelView):
    datamodel = SQLAInterface(LabTodo)
    list_columns = ["id", "subsystem", "text", "done", "uri"]
    add_columns = ["subsystem", "text", "done", "uri"]
    edit_columns = ["subsystem", "text", "done", "uri"]


class ReactPyLabView(BaseView):
    route_base = "/lab"

    @expose("/")
    def index(self):
        # Bettet die ReactPy-Komponente direkt in das FAB-Layout ein
        return self.render_template(
            "appbuilder/baselayout.html",
            content='<iframe src="/reactpy" style="width:100%; height:600
