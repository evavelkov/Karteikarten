"""Karteikarten-Webseite.  Start:  python web/app.py  ->  http://127.0.0.1:5000"""
from datetime import datetime

from flask import Flask, abort, flash, redirect, render_template, request, url_for

from db import close_db, get_db, init_db

app = Flask(__name__)
app.secret_key = "karteikarten-lokal"  # nur für Flash-Meldungen, lokal ausreichend
app.teardown_appcontext(close_db)


# ---------- Hilfsfunktionen ----------

def fetch_one_or_404(sql, *params):
    row = get_db().execute(sql, params).fetchone()
    if row is None:
        abort(404)
    return row


def form_text(field):
    return request.form.get(field, "").strip()


def form_ids(field):
    return [int(v) for v in request.form.getlist(field) if v.isdigit()]


def existing_folder_id(folder_id):
    """Gibt folder_id zurück, wenn der Ordner existiert, sonst None."""
    if folder_id is None:
        return None
    row = get_db().execute("SELECT id FROM folders WHERE id = ?", (folder_id,)).fetchone()
    return row["id"] if row else None


def list_sets(where="", params=()):
    return get_db().execute(
        f"""
        SELECT s.id, s.name, s.description, s.folder_id,
               f.name      AS folder_name,
               COUNT(c.id) AS card_count
        FROM card_sets s
        LEFT JOIN folders f ON f.id = s.folder_id
        LEFT JOIN cards c   ON c.set_id = s.id
        {where}
        GROUP BY s.id
        ORDER BY s.name COLLATE NOCASE
        """,
        params,
    ).fetchall()


def list_folders():
    return get_db().execute(
        "SELECT id, name FROM folders ORDER BY name COLLATE NOCASE"
    ).fetchall()


def move_sets_to_folder(folder_id, set_ids):
    get_db().executemany(
        "UPDATE card_sets SET folder_id = ? WHERE id = ?",
        [(folder_id, set_id) for set_id in set_ids],
    )


def greeting():
    hour = datetime.now().hour
    if hour < 11:
        return "Guten Morgen"
    if hour < 18:
        return "Hallo"
    return "Guten Abend"


# ---------- Startseite ----------

@app.get("/")
def home():
    stats = get_db().execute(
        """
        SELECT (SELECT COUNT(*) FROM folders)   AS folders,
               (SELECT COUNT(*) FROM card_sets) AS sets,
               (SELECT COUNT(*) FROM cards)     AS cards
        """
    ).fetchone()
    return render_template("home.html", stats=stats, greeting=greeting())


# ---------- Ordner ----------

@app.get("/folders")
def folders():
    folders = get_db().execute(
        """
        SELECT f.id, f.name,
               COUNT(DISTINCT s.id) AS set_count,
               COUNT(c.id)          AS card_count
        FROM folders f
        LEFT JOIN card_sets s ON s.folder_id = f.id
        LEFT JOIN cards c     ON c.set_id = s.id
        GROUP BY f.id
        ORDER BY f.name COLLATE NOCASE
        """
    ).fetchall()
    return render_template("folders.html", folders=folders, all_sets=list_sets())


@app.post("/folders")
def create_folder():
    name = form_text("name")
    if not name:
        flash("Bitte einen Ordnernamen eingeben.")
        return redirect(url_for("folders"))
    db = get_db()
    folder_id = db.execute("INSERT INTO folders (name) VALUES (?)", (name,)).lastrowid
    move_sets_to_folder(folder_id, form_ids("set_ids"))
    db.commit()
    return redirect(url_for("folder", folder_id=folder_id))


@app.get("/folders/<int:folder_id>")
def folder(folder_id):
    folder = fetch_one_or_404("SELECT * FROM folders WHERE id = ?", folder_id)
    sets = list_sets("WHERE s.folder_id = ?", (folder_id,))
    other_sets = list_sets("WHERE s.folder_id IS NOT ? ", (folder_id,))
    return render_template("folder.html", folder=folder, sets=sets, other_sets=other_sets)


@app.post("/folders/<int:folder_id>/add-sets")
def add_sets_to_folder(folder_id):
    fetch_one_or_404("SELECT id FROM folders WHERE id = ?", folder_id)
    move_sets_to_folder(folder_id, form_ids("set_ids"))
    get_db().commit()
    return redirect(url_for("folder", folder_id=folder_id))


@app.post("/folders/<int:folder_id>/remove-set/<int:set_id>")
def remove_set_from_folder(folder_id, set_id):
    db = get_db()
    db.execute(
        "UPDATE card_sets SET folder_id = NULL WHERE id = ? AND folder_id = ?",
        (set_id, folder_id),
    )
    db.commit()
    return redirect(url_for("folder", folder_id=folder_id))


@app.post("/folders/<int:folder_id>/rename")
def rename_folder(folder_id):
    fetch_one_or_404("SELECT id FROM folders WHERE id = ?", folder_id)
    name = form_text("name")
    if name:
        db = get_db()
        db.execute("UPDATE folders SET name = ? WHERE id = ?", (name, folder_id))
        db.commit()
    return redirect(url_for("folder", folder_id=folder_id))


@app.post("/folders/<int:folder_id>/delete")
def delete_folder(folder_id):
    folder = fetch_one_or_404("SELECT * FROM folders WHERE id = ?", folder_id)
    db = get_db()
    db.execute("DELETE FROM folders WHERE id = ?", (folder_id,))
    db.commit()
    flash(f"Ordner „{folder['name']}“ wurde gelöscht. Seine Kartensets findest du weiterhin unter „Kartensets“.")
    return redirect(url_for("folders"))


# ---------- Kartensets ----------

@app.get("/sets")
def sets():
    return render_template("sets.html", sets=list_sets())


@app.route("/sets/new", methods=["GET", "POST"])
def new_set():
    if request.method == "GET":
        folder_id = existing_folder_id(request.args.get("folder_id", type=int))
        form = {"name": "", "description": "", "folder_id": folder_id, "cards": [("", "")]}
        return render_template("new_set.html", form=form, folders=list_folders())

    name = form_text("name")
    description = form_text("description")
    folder_id = existing_folder_id(request.form.get("folder_id", type=int))
    pairs = zip(
        (q.strip() for q in request.form.getlist("question")),
        (a.strip() for a in request.form.getlist("answer")),
    )
    cards = [(q, a) for q, a in pairs if q or a]  # komplett leere Zeilen ignorieren

    error = None
    if not name:
        error = "Bitte gib dem Kartenset einen Namen."
    elif any(not q or not a for q, a in cards):
        error = "Jede Karte braucht eine Frage und eine Antwort."
    if error:
        flash(error)
        form = {"name": name, "description": description, "folder_id": folder_id,
                "cards": cards or [("", "")]}
        return render_template("new_set.html", form=form, folders=list_folders()), 400

    db = get_db()
    set_id = db.execute(
        "INSERT INTO card_sets (folder_id, name, description) VALUES (?, ?, ?)",
        (folder_id, name, description),
    ).lastrowid
    db.executemany(
        "INSERT INTO cards (set_id, question, answer) VALUES (?, ?, ?)",
        [(set_id, q, a) for q, a in cards],
    )
    db.commit()
    flash(f"Kartenset „{name}“ mit {len(cards)} Karte{'' if len(cards) == 1 else 'n'} erstellt.")
    return redirect(url_for("card_set", set_id=set_id))


def load_set(set_id):
    return fetch_one_or_404(
        """
        SELECT s.*, f.name AS folder_name
        FROM card_sets s LEFT JOIN folders f ON f.id = s.folder_id
        WHERE s.id = ?
        """,
        set_id,
    )


@app.get("/sets/<int:set_id>")
def card_set(set_id):
    card_set = load_set(set_id)
    cards = get_db().execute(
        "SELECT * FROM cards WHERE set_id = ? ORDER BY id", (set_id,)
    ).fetchall()
    return render_template("set.html", card_set=card_set, cards=cards, folders=list_folders())


@app.post("/sets/<int:set_id>/edit")
def edit_set(set_id):
    card_set = load_set(set_id)
    name = form_text("name") or card_set["name"]
    folder_id = existing_folder_id(request.form.get("folder_id", type=int))
    db = get_db()
    db.execute(
        "UPDATE card_sets SET name = ?, description = ?, folder_id = ? WHERE id = ?",
        (name, form_text("description"), folder_id, set_id),
    )
    db.commit()
    return redirect(url_for("card_set", set_id=set_id))


@app.post("/sets/<int:set_id>/delete")
def delete_set(set_id):
    card_set = load_set(set_id)
    db = get_db()
    db.execute("DELETE FROM card_sets WHERE id = ?", (set_id,))
    db.commit()
    flash(f"Kartenset „{card_set['name']}“ wurde gelöscht.")
    if card_set["folder_id"]:
        return redirect(url_for("folder", folder_id=card_set["folder_id"]))
    return redirect(url_for("sets"))


@app.get("/sets/<int:set_id>/learn")
def learn(set_id):
    card_set = load_set(set_id)
    cards = [
        dict(row)
        for row in get_db().execute(
            "SELECT id, question, answer FROM cards WHERE set_id = ? ORDER BY id",
            (set_id,),
        )
    ]
    return render_template("learn.html", card_set=card_set, cards=cards)


# ---------- Karten ----------

@app.post("/sets/<int:set_id>/cards")
def create_card(set_id):
    load_set(set_id)
    question, answer = form_text("question"), form_text("answer")
    if not question or not answer:
        flash("Frage und Antwort dürfen nicht leer sein.")
    else:
        db = get_db()
        db.execute(
            "INSERT INTO cards (set_id, question, answer) VALUES (?, ?, ?)",
            (set_id, question, answer),
        )
        db.commit()
    return redirect(url_for("card_set", set_id=set_id) + "#neu")


@app.post("/cards/<int:card_id>/edit")
def edit_card(card_id):
    card = fetch_one_or_404("SELECT * FROM cards WHERE id = ?", card_id)
    question, answer = form_text("question"), form_text("answer")
    if question and answer:
        db = get_db()
        db.execute(
            "UPDATE cards SET question = ?, answer = ? WHERE id = ?",
            (question, answer, card_id),
        )
        db.commit()
    else:
        flash("Frage und Antwort dürfen nicht leer sein.")
    return redirect(url_for("card_set", set_id=card["set_id"]) + f"#karte-{card_id}")


@app.post("/cards/<int:card_id>/delete")
def delete_card(card_id):
    card = fetch_one_or_404("SELECT * FROM cards WHERE id = ?", card_id)
    db = get_db()
    db.execute("DELETE FROM cards WHERE id = ?", (card_id,))
    db.commit()
    return redirect(url_for("card_set", set_id=card["set_id"]))


init_db()

if __name__ == "__main__":
    app.run(debug=True)
