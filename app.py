from flask import Flask, render_template, request, redirect, session, send_file
import psycopg2
import psycopg2.extras
from werkzeug.security import generate_password_hash, check_password_hash
from io import BytesIO
from reportlab.pdfgen import canvas
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecret")

def get_db_connection():
    conn = psycopg2.connect(os.environ["DATABASE_URL"], cursor_factory=psycopg2.extras.DictCursor)
    return conn

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        conn.close()
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            return redirect("/dashboard")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        hashed_pw = generate_password_hash(password)
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_pw))
            conn.commit()
        except:
            conn.rollback()
        conn.close()
        return redirect("/")
    return render_template("register.html")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM eleves")
    eleves = cur.fetchall()
    conn.close()
    return render_template("dashboard.html", eleves=eleves)

@app.route("/profil", methods=["GET", "POST"])
def profil():
    if "user_id" not in session:
        return redirect("/")
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == "POST":
        nom = request.form["nom"]
        niveau = request.form["niveau"]
        commentaire = request.form["commentaire"]
        cur.execute("INSERT INTO eleves (nom, niveau, commentaire) VALUES (%s, %s, %s)", (nom, niveau, commentaire))
        conn.commit()
    cur.execute("SELECT * FROM eleves")
    eleves = cur.fetchall()
    conn.close()
    return render_template("profil.html", eleves=eleves)

@app.route("/download/<int:id>")
def download(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM eleves WHERE id = %s", (id,))
    eleve = cur.fetchone()
    conn.close()
    if eleve:
        buffer = BytesIO()
        p = canvas.Canvas(buffer)
        p.drawString(100, 750, "Fiche Élève - EvalIA")
        p.drawString(100, 720, f"Nom : {eleve['nom']}")
        p.drawString(100, 700, f"Niveau : {eleve['niveau']}")
        p.drawString(100, 680, f"Commentaire : {eleve['commentaire']}")
        p.save()
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name=f"{eleve['nom']}_EvalIA.pdf", mimetype="application/pdf")
    return "Élève non trouvé."

@app.route("/suggestions")
def suggestions():
    if "user_id" not in session:
        return redirect("/")
    return render_template("suggestions.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")
