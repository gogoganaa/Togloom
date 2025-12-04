from flask import Flask, render_template_string, request, redirect, url_for, session
import random

app = Flask(__name__)
app.secret_key = "change_this_to_any_random_secret_key"  # Session-д хэрэгтэй


# --- Зураг таах тоглоомын асуултууд ---
IMAGE_QUIZ = [
    {
        "image": "https://upload.wikimedia.org/wikipedia/commons/1/1b/Horse_in_a_field.jpg",
        "question": "Энэ зураг дээр ямар мал байна вэ?",
        "options": ["Үхэр", "Морь", "Хонь"],
        "answer": "Морь"
    },
    {
        "image": "https://upload.wikimedia.org/wikipedia/commons/8/8c/Cow_female_black_white.jpg",
        "question": "Энэ зураг дээр юу байна вэ?",
        "options": ["Үхэр", "Тэмээ", "Ямаа"],
        "answer": "Үхэр"
    },
    {
        "image": "https://upload.wikimedia.org/wikipedia/commons/1/1c/Sheep_in_a_field.jpg",
        "question": "Энэ зураг дээр ямар мал байна вэ?",
        "options": ["Ямаа", "Тэмээ", "Хонь"],
        "answer": "Хонь"
    },
]

# --- Төөрдөг байшин (maze) ---
# 0 = чөлөөтэй, 1 = хананд тулсан
MAZE_GRID = [
    [0, 0, 1, 0, 0],
    [1, 0, 1, 0, 1],
    [0, 0, 0, 0, 1],
    [0, 1, 1, 0, 0],
    [0, 0, 0, 1, 0],
]
MAZE_START = (0, 0)
MAZE_GOAL = (4, 4)


# --- Нийт layout HTML ---
BASE_HTML = """
<!doctype html>
<html lang="mn">
<head>
    <meta charset="utf-8">
    <title>{{ page_title }} - Миний тоглоомын веб</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <!-- Bootstrap 5 CDN -->
    <link
      href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
      rel="stylesheet"
    >
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">

    <style>
        body {
            font-family: 'Poppins', sans-serif;
            min-height: 100vh;
            background: linear-gradient(135deg, #1f2933, #111827);
            color: #f9fafb;
        }
        .navbar {
            background: rgba(15, 23, 42, 0.95) !important;
            backdrop-filter: blur(10px);
        }
        .game-card, .content-card {
            background: linear-gradient(135deg, #020617, #111827);
            border-radius: 1.25rem;
            border: 1px solid rgba(148, 163, 184, 0.3);
            box-shadow: 0 20px 40px rgba(15, 23, 42, 0.7);
        }
        .game-card:hover {
            transform: translateY(-4px);
            transition: 0.2s ease-in-out;
            box-shadow: 0 24px 60px rgba(15, 23, 42, 0.9);
        }
        .btn-gradient {
            border-radius: 9999px;
            border: none;
            padding-inline: 1.5rem;
            background: linear-gradient(135deg, #ec4899, #8b5cf6);
            color: white;
            font-weight: 600;
        }
        .btn-gradient:hover {
            filter: brightness(1.1);
        }
        .badge-soft {
            background: rgba(148, 163, 184, 0.2);
            border-radius: 9999px;
            padding: 0.25rem 0.75rem;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        footer {
            color: #9ca3af;
            font-size: 0.8rem;
        }
        /* Maze style */
        .maze-grid {
            display: grid;
            grid-template-columns: repeat(5, 40px);
            grid-template-rows: repeat(5, 40px);
            gap: 4px;
            margin: 1rem auto;
        }
        .maze-cell {
            width: 40px;
            height: 40px;
            border-radius: 0.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.9rem;
            font-weight: 600;
        }
        .maze-wall {
            background: #111827;
            border: 1px solid #4b5563;
        }
        .maze-path {
            background: #020617;
            border: 1px solid #374151;
        }
        .maze-start {
            background: #22c55e;
            border: 1px solid #4ade80;
        }
        .maze-goal {
            background: #eab308;
            border: 1px solid #facc15;
        }
        .maze-current {
            background: #3b82f6;
            border: 1px solid #60a5fa;
        }
        img.quiz-image {
            max-height: 260px;
            object-fit: cover;
        }
    </style>
</head>
<body>
<nav class="navbar navbar-expand-lg navbar-dark border-bottom border-secondary">
  <div class="container">
    <a class="navbar-brand fw-bold" href="{{ home_url }}">🎮 Миний тоглоомын веб</a>
    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#mainNav">
      <span class="navbar-toggler-icon"></span>
    </button>
    <div class="collapse navbar-collapse" id="mainNav">
      <ul class="navbar-nav ms-auto mb-2 mb-lg-0 small">
        <li class="nav-item"><a class="nav-link {% if active_page == 'home' %}active{% endif %}" href="{{ home_url }}">Нүүр</a></li>
        <li class="nav-item"><a class="nav-link {% if active_page == 'guess' %}active{% endif %}" href="{{ guess_url }}">Санасан тоо</a></li>
        <li class="nav-item"><a class="nav-link {% if active_page == 'rps' %}active{% endif %}" href="{{ rps_url }}">Хайч-Чулуу-Даавуу</a></li>
        <li class="nav-item"><a class="nav-link {% if active_page == 'image' %}active{% endif %}" href="{{ image_url }}">Зураг таах</a></li>
        <li class="nav-item"><a class="nav-link {% if active_page == 'fib' %}active{% endif %}" href="{{ fib_url }}">Фибоначчи</a></li>
        <li class="nav-item"><a class="nav-link {% if active_page == 'maze' %}active{% endif %}" href="{{ maze_url }}">Төөрдөг байшин</a></li>
      </ul>
    </div>
  </div>
</nav>

<main class="container py-4 py-lg-5">
  {{ content|safe }}
</main>

<footer class="container pb-4">
  <div class="d-flex justify-content-between flex-wrap">
    <span>© {{ year }} Миний жижиг тоглоомууд</span>
    <span>Flask + Python ашигласан сургалтын веб</span>
  </div>
</footer>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""


def render_page(title, content_html, active_page="home"):
    return render_template_string(
        BASE_HTML,
        page_title=title,
        content=content_html,
        active_page=active_page,
        home_url=url_for("home"),
        guess_url=url_for("guess_number"),
        rps_url=url_for("rock_paper_scissors"),
        image_url=url_for("image_quiz"),
        fib_url=url_for("fibonacci_puzzle"),
        maze_url=url_for("maze_game"),
        year=2025,
    )


# --- Нүүр хуудас ---
@app.route("/")
def home():
    content = """
    <div class="row g-4 align-items-stretch">
      <div class="col-lg-4">
        <div class="content-card p-4 h-100">
          <div class="badge-soft mb-2">Python + Flask</div>
          <h1 class="h3 fw-bold mb-3">Жижиг тоглоомуудын хуримтлал 🎮</h1>
          <p class="mb-3">
            Энэ веб нь Python-оор бичигдсэн backend-тэй 5 өөр тоглоом агуулсан.
            VS Code дээрээс локал орчинд ажиллуулж, сургалтанд ашиглаж болно.
          </p>
          <ul class="small mb-3">
            <li>Санасан тоог таах</li>
            <li>Хайч – Чулуу – Даавуу</li>
            <li>Зураг таах</li>
            <li>Фибоначчигийн тоон таавар</li>
            <li>Жижиг төөрдөг байшин</li>
          </ul>
          <a href="{guess}" class="btn btn-gradient me-2 mb-2">Тоглож эхлэх</a>
          <span class="text-secondary small d-block">Навигац дээрээс тоглоом бүр рүү орж болно.</span>
        </div>
      </div>
      <div class="col-lg-8">
        <div class="row g-4">
          <div class="col-md-6">
            <a href="{guess}" class="text-decoration-none text-reset">
              <div class="game-card p-3 h-100">
                <h2 class="h5 fw-semibold mb-1">1. Санасан тоог таах</h2>
                <p class="small mb-0">Компьютер 1-100 хооронд санамсаргүй тоо САНАНА. Та хэдэн удаад олж чадах вэ?</p>
              </div>
            </a>
          </div>
          <div class="col-md-6">
            <a href="{rps}" class="text-decoration-none text-reset">
              <div class="game-card p-3 h-100">
                <h2 class="h5 fw-semibold mb-1">2. Хайч – Чулуу – Даавуу</h2>
                <p class="small mb-0">Сонголтоо хийгээд компьютертой өрсөлдөөрэй. Ялагчийг Python шийднэ.</p>
              </div>
            </a>
          </div>
          <div class="col-md-6">
            <a href="{image}" class="text-decoration-none text-reset">
              <div class="game-card p-3 h-100">
                <h2 class="h5 fw-semibold mb-1">3. Зураг таах</h2>
                <p class="small mb-0">Малын зураг хараад зөв хариуг сонгоорой. Сургалтын зориулалттай энгийн quiz.</p>
              </div>
            </a>
          </div>
          <div class="col-md-6">
            <a href="{fib}" class="text-decoration-none text-reset">
              <div class="game-card p-3 h-100">
                <h2 class="h5 fw-semibold mb-1">4. Фибоначчигийн таавар</h2>
                <p class="small mb-0">Фибоначчигийн дарааллын дараагийн гишүүнийг тааж, логик сэтгэлгээгээ хөгжүүл.</p>
              </div>
            </a>
          </div>
          <div class="col-md-12">
            <a href="{maze}" class="text-decoration-none text-reset">
              <div class="game-card p-3 h-100">
                <h2 class="h5 fw-semibold mb-1">5. Төөрдөг байшин</h2>
                <p class="small mb-0">Жижиг 5×5 maze-д алхаа чиглэлээ сонгон, гарахад хүрч чадах уу?</p>
              </div>
            </a>
          </div>
        </div>
      </div>
    </div>
    """.format(
        guess=url_for("guess_number"),
        rps=url_for("rock_paper_scissors"),
        image=url_for("image_quiz"),
        fib=url_for("fibonacci_puzzle"),
        maze=url_for("maze_game"),
    )
    return render_page("Нүүр", content, active_page="home")


# --- 1. Санасан тоог таах ---
@app.route("/guess-number", methods=["GET", "POST"])
def guess_number():
    if "secret_number" not in session:
        session["secret_number"] = random.randint(1, 100)
        session["guess_attempts"] = 0

    message = "Би 1-100 хооронд нэг тоо саналаа. Та таагаад үзээрэй!"
    last_result = ""
    last_guess = ""

    if request.method == "POST":
        guess_str = request.form.get("guess", "").strip()
        if guess_str.isdigit():
            guess = int(guess_str)
            secret = session.get("secret_number")
            session["guess_attempts"] = session.get("guess_attempts", 0) + 1
            last_guess = str(guess)

            if guess < secret:
                last_result = "Жижиг байна. Том тоо оролдоод үз! 🔼"
            elif guess > secret:
                last_result = "Хэт том байна. Жаахан багасга! 🔽"
            else:
                last_result = f"🎉 Баяр хүргэе! Та {session['guess_attempts']} удаад зөв таалаа. Шинэ тоо саналаа."
                # Шинэ тоглоом эхлүүлэх
                session["secret_number"] = random.randint(1, 100)
                session["guess_attempts"] = 0
        else:
            last_result = "Зөвхөн бүхэл тоо оруулна уу."

    attempts = session.get("guess_attempts", 0)

    content = f"""
    <div class="content-card p-4 p-lg-5 mx-auto" style="max-width: 540px;">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h1 class="h4 fw-semibold mb-0">1. Санасан тоог таах</h1>
        <span class="badge-soft">1–100 хооронд</span>
      </div>
      <p class="small text-secondary mb-4">{message}</p>
      <form method="post" class="row g-2 align-items-center">
        <div class="col-12 col-sm-8">
          <input type="number" min="1" max="100" name="guess" value="{last_guess}" class="form-control form-control-lg" placeholder="Таамагласан тоо" required>
        </div>
        <div class="col-12 col-sm-4 d-grid">
          <button class="btn btn-gradient btn-lg" type="submit">ТААХ</button>
        </div>
      </form>
      <div class="mt-3">
        <p class="mb-1 small text-secondary">Одоогийн оролдлого: <strong>{attempts}</strong></p>
        <p class="fw-semibold">{last_result}</p>
      </div>
      <hr class="border-secondary my-4">
      <p class="small text-secondary mb-0">
        Жич: Та зөв таавал автоматаар шинэ тоо санаж дахин тоглоом үргэлжилнэ.
      </p>
    </div>
    """

    return render_page("Санасан тоо", content, active_page="guess")


# --- 2. Хайч, Чулуу, Даавуу ---
@app.route("/rps", methods=["GET", "POST"])
def rock_paper_scissors():
    choices = ["Хайч", "Чулуу", "Даавуу"]
    user_choice = ""
    computer_choice = ""
    result = "Сонголтоо хийгээд тоглож эхлээрэй."

    if request.method == "POST":
        user_choice = request.form.get("choice")
        if user_choice in choices:
            computer_choice = random.choice(choices)

            # Ялалт тогтоох
            if user_choice == computer_choice:
                result = "Тэнцлээ 🤝"
            elif (
                (user_choice == "Хайч" and computer_choice == "Даавуу")
                or (user_choice == "Даавуу" and computer_choice == "Чулуу")
                or (user_choice == "Чулуу" and computer_choice == "Хайч")
            ):
                result = "Та хожлоо! 🎉"
            else:
                result = "Компьютер хожлоо 😅"
        else:
            result = "Алдаа: буруу сонголт."

    buttons_html = ""
    for c in choices:
        buttons_html += f"""
        <button type="submit" name="choice" value="{c}" class="btn btn-outline-light flex-fill">
          {c}
        </button>
        """

    content = f"""
    <div class="content-card p-4 p-lg-5 mx-auto" style="max-width: 540px;">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h1 class="h4 fw-semibold mb-0">2. Хайч – Чулуу – Даавуу</h1>
        <span class="badge-soft">Classic game</span>
      </div>
      <p class="small text-secondary mb-4">
        Дуртайгаа сонго, компьютер санамсаргүйгээр нэгийг сонгоно. Ялагчийг Python тооцно.
      </p>
      <form method="post" class="d-flex gap-2 mb-3">
        {buttons_html}
      </form>
      <div class="border border-secondary rounded-4 p-3">
        <p class="mb-1 small text-secondary">Таны сонголт: <strong>{user_choice or "-"}</strong></p>
        <p class="mb-1 small text-secondary">Компьютер: <strong>{computer_choice or "-"}</strong></p>
        <p class="fw-semibold mt-2">{result}</p>
      </div>
    </div>
    """

    return render_page("Хайч, Чулуу, Даавуу", content, active_page="rps")


# --- 3. Зураг таах ---
@app.route("/image-quiz", methods=["GET", "POST"])
def image_quiz():
    if "quiz_index" not in session:
        session["quiz_index"] = 0

    idx = session["quiz_index"]
    if idx >= len(IMAGE_QUIZ):
        idx = 0
        session["quiz_index"] = 0

    q = IMAGE_QUIZ[idx]
    selected = ""
    feedback = "Зураг хараад зөв хариултыг сонгоорой."

    if request.method == "POST":
        selected = request.form.get("answer", "")
        if selected:
            if selected == q["answer"]:
                feedback = "🎉 Зөв хариуллаа!"
                # Дараагийн асуулт руу шилжих
                session["quiz_index"] = session["quiz_index"] + 1
            else:
                feedback = "Буруу байна. Ахин оролдоод үзээрэй 🙂"

    options_html = ""
    for opt in q["options"]:
        checked = "checked" if opt == selected else ""
        options_html += f"""
        <div class="form-check">
          <input class="form-check-input" type="radio" name="answer" id="opt_{opt}" value="{opt}" {checked} required>
          <label class="form-check-label" for="opt_{opt}">
            {opt}
          </label>
        </div>
        """

    content = f"""
    <div class="content-card p-4 p-lg-5 mx-auto" style="max-width: 720px;">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h1 class="h4 fw-semibold mb-0">3. Зураг таах</h1>
        <span class="badge-soft">Сургалтын quiz</span>
      </div>
      <p class="small text-secondary mb-3">
        Малын зураг хараад ямар мал байгааг таана. Зөв хариу сонгосон тохиолдолд дараагийн асуулт руу автоматаар шилжинэ.
      </p>
      <div class="row g-4 align-items-center">
        <div class="col-md-6">
          <img src="{q['image']}" alt="Таах зураг" class="img-fluid rounded-4 shadow quiz-image">
        </div>
        <div class="col-md-6">
          <form method="post">
            <p class="fw-semibold mb-2">{q['question']}</p>
            {options_html}
            <button type="submit" class="btn btn-gradient mt-3">Илгээх</button>
          </form>
          <p class="mt-3 fw-semibold">{feedback}</p>
        </div>
      </div>
    </div>
    """

    return render_page("Зураг таах", content, active_page="image")


# --- 4. Фибоначчигийн таавар ---
def generate_fibonacci_puzzle():
    # 0,1,1,2,3,5,8,13,...
    length = random.randint(5, 7)
    seq = [0, 1]
    for _ in range(2, length + 1):
        seq.append(seq[-1] + seq[-2])
    # Жишээ нь эхний length тоог харуулж, дараагийн гишүүнийг таалгана
    visible = seq[:length]
    answer = seq[length]
    return visible, answer


@app.route("/fibonacci", methods=["GET", "POST"])
def fibonacci_puzzle():
    if "fib_seq" not in session or "fib_answer" not in session:
        seq, ans = generate_fibonacci_puzzle()
        session["fib_seq"] = seq
        session["fib_answer"] = ans

    seq = session["fib_seq"]
    answer = session["fib_answer"]

    feedback = "Фибоначчигийн дарааллын дараагийн гишүүнийг таагаарай."
    user_answer = ""

    if request.method == "POST":
        user_str = request.form.get("fib_answer", "").strip()
        user_answer = user_str
        if user_str.isdigit():
            if int(user_str) == answer:
                feedback = f"🎉 Зөв! Дараагийн гишүүн нь {answer}. Шинэ бодлого гаргалаа."
                # Шинэ бодлого
                seq, ans = generate_fibonacci_puzzle()
                session["fib_seq"] = seq
                session["fib_answer"] = ans
                seq = seq
                answer = ans
                user_answer = ""
            else:
                feedback = "Буруу байна. Дахин бодоод үзээрэй 🙂"
        else:
            feedback = "Зөвхөн бүхэл тоо оруулна уу."

    seq_str = ", ".join(str(x) for x in seq)

    content = f"""
    <div class="content-card p-4 p-lg-5 mx-auto" style="max-width: 640px;">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h1 class="h4 fw-semibold mb-0">4. Фибоначчигийн таавар</h1>
        <span class="badge-soft">Математик логик</span>
      </div>
      <p class="small text-secondary mb-3">
        Фибоначчигийн дараалалд дараагийн гишүүн нь өмнөх хоёр гишүүний нийлбэр байдаг.
      </p>
      <div class="border border-secondary rounded-4 p-3 mb-3">
        <p class="mb-1 small text-secondary">Өгөгдсөн дараалал:</p>
        <p class="fw-semibold mb-0"> {seq_str}, <span class="text-secondary">...</span></p>
      </div>
      <form method="post" class="row g-2 align-items-center">
        <div class="col-12 col-sm-8">
          <label class="form-label small text-secondary mb-1">Дараагийн гишүүн:</label>
          <input type="number" name="fib_answer" value="{user_answer}" class="form-control form-control-lg" placeholder="Хариу" required>
        </div>
        <div class="col-12 col-sm-4 d-grid">
          <button class="btn btn-gradient btn-lg mt-sm-4" type="submit">Шалгах</button>
        </div>
      </form>
      <p class="mt-3 fw-semibold">{feedback}</p>
    </div>
    """

    return render_page("Фибоначчи", content, active_page="fib")


# --- 5. Төөрдөг байшин ---
@app.route("/maze", methods=["GET", "POST"])
def maze_game():
    # Эхлэх байрлалыг session-д хадгална
    if "maze_pos" not in session:
        session["maze_pos"] = MAZE_START

    message = "START нүднээс GOAL нүд рүү хүрэхийн тулд чиглэлээ сонгон алх."
    reached_goal = False

    if request.method == "POST":
        move = request.form.get("move")
        row, col = session["maze_pos"]

        dr = dc = 0
        if move == "up":
            dr = -1
        elif move == "down":
            dr = 1
        elif move == "left":
            dc = -1
        elif move == "right":
            dc = 1

        new_r = row + dr
        new_c = col + dc

        # Хил болон хананы шалгалт
        if 0 <= new_r < len(MAZE_GRID) and 0 <= new_c < len(MAZE_GRID[0]) and MAZE_GRID[new_r][new_c] == 0:
            session["maze_pos"] = (new_r, new_c)
            row, col = new_r, new_c
        else:
            message = "Хана эсвэл хүрээнээс гарах гэж байна. Өөр чиглэл сонгоно уу 🙂"

        if (row, col) == MAZE_GOAL:
            message = "🎉 Та амжилттай гарахад хүрлээ! Шинэ тоглоом эхэллээ."
            reached_goal = True
            session["maze_pos"] = MAZE_START

    current_r, current_c = session["maze_pos"]

    # Maze-г HTML болгон зурна
    cells_html = ""
    for r in range(len(MAZE_GRID)):
        for c in range(len(MAZE_GRID[0])):
            cell = MAZE_GRID[r][c]
            cell_class = "maze-path"
            label = ""

            if cell == 1:
                cell_class = "maze-wall"
            if (r, c) == MAZE_START:
                cell_class = "maze-start"
                label = "S"
            if (r, c) == MAZE_GOAL:
                cell_class = "maze-goal"
                label = "G"
            if (r, c) == (current_r, current_c):
                cell_class = "maze-current"
                label = "🙂" if not reached_goal else "⭐"

            cells_html += f'<div class="maze-cell {cell_class}">{label}</div>'

    content = f"""
    <div class="content-card p-4 p-lg-5 mx-auto" style="max-width: 640px;">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h1 class="h4 fw-semibold mb-0">5. Төөрдөг байшин</h1>
        <span class="badge-soft">5×5 maze</span>
      </div>
      <p class="small text-secondary mb-3">
        START (S) нүднээс GOAL (G) нүд хүртэл хүрэхийг хичээгээрэй. Цэнхэр смайли бол таны одоогийн байрлал.
      </p>
      <div class="maze-grid">
        {cells_html}
      </div>
      <form method="post" class="d-flex flex-wrap gap-2 justify-content-center mt-3">
        <button type="submit" name="move" value="up" class="btn btn-outline-light btn-sm px-3">Дээш ↑</button>
        <button type="submit" name="move" value="left" class="btn btn-outline-light btn-sm px-3">← Зүүн</button>
        <button type="submit" name="move" value="right" class="btn btn-outline-light btn-sm px-3">Баруун →</button>
        <button type="submit" name="move" value="down" class="btn btn-outline-light btn-sm px-3">Доош ↓</button>
      </form>
      <p class="mt-3 fw-semibold">{message}</p>
    </div>
    """

    return render_page("Төөрдөг байшин", content, active_page="maze")


if __name__ == "__main__":
    # debug=True байвал өөрчлөлт хадгалахад автоматаар restart хийнэ
    app.run(debug=True)
