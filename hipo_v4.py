from tkinter import *
import random
import math
from pathlib import Path
import time



SIRINA, VISINA = 1000, 700
FPS = 30

HIPO_X, HIPO_Y = SIRINA // 2, 120
HIPO_POCETNA_VELICINA = 130.0
HIPO_MAX_VELICINA = 500.0
HIPO_POSTOTAK_RASTA = 1.03
HIPO_BRZINA_KRETANJA = 3
TOP_BRZINA = 7
VOCE_BRZINA = 10
RAZMAK_AUTOMATSKOG_PUCANJA = 500

BASE_DIR = Path(__file__).resolve().parent

try:
    from PIL import Image, ImageTk
    PIL_DOSTUPAN = True
except ImportError:
    PIL_DOSTUPAN = False


prozor = Tk()
prozor.title("Hipo Space Shooter")
prozor.resizable(False, False)

platno = Canvas(
    prozor,
    width=SIRINA,
    height=VISINA,
    bg="#87CEEB",
    highlightthickness=0
)
platno.pack()


def putanja(naziv):
    return BASE_DIR / naziv


def ucitaj_tk_sliku(naziv):
    try:
        return PhotoImage(file=str(putanja(naziv)))
    except TclError:
        print(f"Upozorenje: ne mogu učitati {naziv}.")
        return None

hipo_original = ucitaj_tk_sliku("mali.png")
jabuka_original = ucitaj_tk_sliku("jabuka.png")
lubenica_original = ucitaj_tk_sliku("lubenica.png")

top_kadrovi = []

try:
    if PIL_DOSTUPAN:
        with Image.open(putanja("cannon.gif")) as im:
            try:
                i = 0
                while True:
                    im.seek(i)
                    frame = im.convert("RGBA").resize((70, 70), Image.Resampling.LANCZOS)
                    top_kadrovi.append(ImageTk.PhotoImage(frame))
                    i += 1
            except EOFError:
                pass

    if not top_kadrovi:
        gif = PhotoImage(file=str(putanja("cannon.gif")))
        indeks = 0

        while True:
            try:
                kadar = PhotoImage(
                    file=str(putanja("cannon.gif")),
                    format=f"gif -index {indeks}"
                )
                top_kadrovi.append(kadar)
                indeks += 1
            except TclError:
                break

        if not top_kadrovi:
            top_kadrovi = [gif]

except TclError:
    print("Upozorenje: ne mogu učitati cannon.gif.")

eksplozija_kadrovi = []

try:
    if PIL_DOSTUPAN:
        with Image.open(putanja("eksplozija.gif")) as im:
            try:
                i = 0
                while True:
                    im.seek(i)
                    frame = im.convert("RGBA").resize((300, 300), Image.Resampling.LANCZOS)
                    eksplozija_kadrovi.append(ImageTk.PhotoImage(frame))
                    i += 1
            except EOFError:
                pass

    if not eksplozija_kadrovi:
        gif_eksplozija = PhotoImage(file=str(putanja("eksplozija.gif")))
        indeks = 0

        while True:
            try:
                kadar = PhotoImage(
                    file=str(putanja("eksplozija.gif")),
                    format=f"gif -index {indeks}"
                )
                eksplozija_kadrovi.append(kadar)
                indeks += 1
            except TclError:
                break

        if not eksplozija_kadrovi:
            eksplozija_kadrovi = [gif_eksplozija]

except TclError:
    print("Upozorenje: ne mogu učitati eksplozija.gif.")


def tk_slika_velicine(original, sirina, visina):
    if original is None:
        return None

    sirina = max(1, int(sirina))
    visina = max(1, int(visina))

    faktor_x = max(1, round(sirina / max(1, original.width())))
    faktor_y = max(1, round(visina / max(1, original.height())))

    return original.zoom(faktor_x, faktor_y)


def ucitaj_skaliranu_sliku(naziv, sirina, visina):
    if PIL_DOSTUPAN:
        try:
            with Image.open(putanja(naziv)) as izvor:
                slika = izvor.convert("RGBA")
                slika = slika.resize(
                    (max(1, int(sirina)), max(1, int(visina))),
                    Image.Resampling.LANCZOS
                )
                return ImageTk.PhotoImage(slika)
        except Exception as e:
            print(f"Greška pri skaliranju {naziv}: {e}")

    original = ucitaj_tk_sliku(naziv)
    return tk_slika_velicine(original, sirina, visina)


# Stanje igre
igra_pokrenuta = False
hipo_velicina = HIPO_POCETNA_VELICINA
hipo_prikaz = None
hipo_prikaz_velicina = None
hipo_smjer = 1

top_x, top_y = SIRINA // 2, VISINA - 100

pritisnute_tipke = set()
voce = []
prepreke = []

igra_traje = False
pobjeda = False
frame_topa = 0
frame_eksplozije = 0
animacija_id = None

vrijeme_pocetka = 0
proteklo_vrijeme = 0

slike_voca = {}

for naziv, original in (
    ("jabuka", jabuka_original),
    ("lubenica", lubenica_original)
):
    if original is not None:
        if PIL_DOSTUPAN:
            try:
                with Image.open(putanja(f"{naziv}.png")) as izvor:
                    im = izvor.convert("RGBA")
                    im = im.resize(
                        (50, 50),
                        Image.Resampling.LANCZOS
                    )
                    slike_voca[naziv] = ImageTk.PhotoImage(im)
            except Exception:
                slike_voca[naziv] = original
        else:
            slike_voca[naziv] = original


def pomakni_hipo():
    global HIPO_X, hipo_smjer

    HIPO_X += HIPO_BRZINA_KRETANJA * hipo_smjer

    pola_sirine = hipo_velicina / 2
    if HIPO_X - pola_sirine < 50:
        HIPO_X = pola_sirine + 50
        hipo_smjer = 1
    elif HIPO_X + pola_sirine > SIRINA - 50:
        HIPO_X = SIRINA - pola_sirine - 50
        hipo_smjer = -1

    if random.random() < 0.03:
        hipo_smjer = random.choice([-1, 1])


def nacrtaj_hipo():
    global hipo_prikaz, hipo_prikaz_velicina

    platno.delete("hipo")

    if hipo_original is not None:
        cilj = int(hipo_velicina)

        if (
            hipo_prikaz is None
            or hipo_prikaz_velicina != cilj
        ):
            hipo_prikaz = ucitaj_skaliranu_sliku(
                "mali.png",
                cilj,
                cilj
            )
            hipo_prikaz_velicina = cilj

        if hipo_prikaz is not None:
            platno.create_image(
                HIPO_X,
                HIPO_Y,
                image=hipo_prikaz,
                tags="hipo"
            )
            return

    r = hipo_velicina / 2

    platno.create_oval(
        HIPO_X - r,
        HIPO_Y - r,
        HIPO_X + r,
        HIPO_Y + r,
        fill="#a86fa8",
        outline="#5c365c",
        width=4,
        tags="hipo"
    )

    platno.create_text(
        HIPO_X,
        HIPO_Y,
        text="HIPO",
        fill="white",
        font=("Arial", 16, "bold"),
        tags="hipo"
    )


def nacrtaj_top():
    global frame_topa

    platno.delete("top")

    if top_kadrovi:
        kadar = top_kadrovi[frame_topa % len(top_kadrovi)]

        platno.create_image(
            top_x,
            top_y,
            image=kadar,
            tags="top"
        )

        frame_topa += 1

    else:
        platno.create_rectangle(
            top_x - 35,
            top_y - 20,
            top_x + 35,
            top_y + 20,
            fill="#555555",
            outline="black",
            tags="top"
        )

        platno.create_rectangle(
            top_x - 10,
            top_y - 45,
            top_x + 10,
            top_y - 15,
            fill="#333333",
            outline="black",
            tags="top"
        )


def pucaj(event=None):
    if not igra_traje:
        return

    tip = random.choice(["jabuka", "lubenica"])

    voce.append({
        "x": top_x,
        "y": top_y - 45,
        "tip": tip,
        "brzina": VOCE_BRZINA,
        "velicina": 25,
        "slika": slike_voca.get(tip)
    })


def nacrtaj_voce():
    platno.delete("voce")

    for v in voce:
        if v["slika"] is not None:
            platno.create_image(
                v["x"],
                v["y"],
                image=v["slika"],
                tags="voce"
            )
        else:
            boja = (
                "#e53935"
                if v["tip"] == "jabuka"
                else "#2e9d50"
            )

            platno.create_oval(
                v["x"] - v["velicina"],
                v["y"] - v["velicina"],
                v["x"] + v["velicina"],
                v["y"] + v["velicina"],
                fill=boja,
                outline="white",
                width=2,
                tags="voce"
            )


def stvori_prepreku():
    if not igra_traje:
        return

    x = random.randint(45, SIRINA - 45)
    tip = random.choice(["asteroid", "planet", "meteor"])

    prepreke.append({
        "x": x,
        "y": -45,
        "velicina": random.randint(20, 36),
        "brzina": random.randint(3, 7),
        "tip": tip
    })


def nacrtaj_prepreke():
    platno.delete("prepreka")

    for p in prepreke:
        x, y, r = p["x"], p["y"], p["velicina"]

        if p["tip"] == "asteroid":
            platno.create_polygon(
                x-r, y-r//2,
                x-r//2, y-r,
                x+r//2, y-r,
                x+r, y-r//3,
                x+r//2, y+r,
                x-r//2, y+r//2,
                fill="#686868",
                outline="#353535",
                width=3,
                tags="prepreka"
            )

            platno.create_oval(
                x-7, y-4,
                x+2, y+5,
                fill="#444444",
                outline="",
                tags="prepreka"
            )

        elif p["tip"] == "planet":
            platno.create_oval(
                x-r, y-r,
                x+r, y+r,
                fill="#d77b45",
                outline="#783f2a",
                width=3,
                tags="prepreka"
            )

            platno.create_arc(
                x-r, y-r//2,
                x+r, y+r//2,
                start=190,
                extent=160,
                style=ARC,
                outline="#f0c27b",
                width=4,
                tags="prepreka"
            )

        else:
            platno.create_polygon(
                x, y-r,
                x+r, y+r,
                x-r, y+r,
                fill="#b34b36",
                outline="#6d2924",
                width=3,
                tags="prepreka"
            )


def pomakni_top():
    global top_x, top_y

    if "a" in pritisnute_tipke:
        top_x -= TOP_BRZINA

    if "d" in pritisnute_tipke:
        top_x += TOP_BRZINA

    if "w" in pritisnute_tipke:
        top_y -= TOP_BRZINA

    if "s" in pritisnute_tipke:
        top_y += TOP_BRZINA

    top_x = max(40, min(SIRINA - 40, top_x))
    top_y = max(VISINA // 2, min(VISINA - 50, top_y))


def pomakni_voce():
    global hipo_velicina, hipo_prikaz_velicina

    for v in voce[:]:
        v["y"] -= v["brzina"]

        pogodilo_prepreku = False

        for p in prepreke:
            if math.hypot(
                v["x"] - p["x"],
                v["y"] - p["y"]
            ) <= v["velicina"] + p["velicina"]:
                pogodilo_prepreku = True
                break

        if pogodilo_prepreku:
            voce.remove(v)
            continue

        unutar_sirine = abs(v["x"] - HIPO_X) <= (hipo_velicina / 2)
        dosegao_polovicu_visine = v["y"] <= HIPO_Y

        dodiruje_hipa = unutar_sirine and dosegao_polovicu_visine

        if dodiruje_hipa:
            stara_velicina_int = int(hipo_velicina)

            hipo_velicina = min(
                HIPO_MAX_VELICINA,
                hipo_velicina * HIPO_POSTOTAK_RASTA
            )

            if int(hipo_velicina) != stara_velicina_int:
                hipo_prikaz_velicina = None

            voce.remove(v)

            if hipo_velicina >= HIPO_MAX_VELICINA:
                pobjedi()
                return

        elif v["y"] < -60:
            voce.remove(v)


def pomakni_prepreke():
    for p in prepreke:
        p["y"] += p["brzina"]

    prepreke[:] = [
        p for p in prepreke
        if p["y"] < VISINA + 60
    ]


def provjeri_sudar():
    for p in prepreke:
        if math.hypot(
            top_x - p["x"],
            top_y - p["y"]
        ) < 35 + p["velicina"] * 0.65:
            izgubi()
            return

gumb_igraj = None

def ukloni_gumbe():
    global gumb_igraj
    if gumb_igraj is not None:
        gumb_igraj.destroy()
        gumb_igraj = None


def prikazi_pocetni_ekran():
    global igra_traje, igra_pokrenuta, gumb_igraj, animacija_id
    igra_traje = False
    igra_pokrenuta = False

    if animacija_id is not None:
        prozor.after_cancel(animacija_id)
        animacija_id = None

    platno.delete("all")
    ukloni_gumbe()

    tekst_upute = (
        "Za upravljanje koristi WASD tipke na tipkovnici:\n"
        "- W – kretanje prema gore\n"
        "- A – kretanje ulijevo\n"
        "- S – kretanje prema dolje\n"
        "- D – kretanje udesno\n"
        "Izbjegavaj prepreke i hrani HIPO-a voćem!"
    )

    platno.create_text(
        SIRINA // 2,
        VISINA // 2 - 100,
        text=tekst_upute,
        fill="white",
        font=("Arial", 20, "bold"),
        justify="center",
        tags="upute"
    )

    gumb_igraj = Button(
        prozor,
        text="IGRAJ",
        font=("Arial", 24, "bold"),
        bg="#4CAF50",
        fg="white",
        activebackground="#45a049",
        activeforeground="white",
        relief="raised",
        bd=5,
        command=pokreni_igru
    )
    platno.create_window(SIRINA // 2, VISINA // 2 + 130, window=gumb_igraj, width=220, height=60)


def pokreni_igru():
    global igra_traje, igra_pokrenuta, hipo_velicina, hipo_prikaz_velicina, voce, prepreke, top_x, top_y, HIPO_X, hipo_smjer, vrijeme_pocetka, animacija_id
    ukloni_gumbe()
    
    if animacija_id is not None:
        prozor.after_cancel(animacija_id)
        animacija_id = None

    platno.delete("all")
    
    hipo_velicina = HIPO_POCETNA_VELICINA
    hipo_prikaz_velicina = None
    HIPO_X = SIRINA // 2
    hipo_smjer = 1
    voce.clear()
    prepreke.clear()
    top_x, top_y = SIRINA // 2, VISINA - 100
    
    vrijeme_pocetka = time.time()
    
    igra_pokrenuta = True
    igra_traje = True

    nacrtaj_hipo()
    nacrtaj_top()
    stvaraj_prepreke()
    automatski_pucaj()
    igra()


def animiraj_eksploziju():
    global frame_eksplozije, animacija_id
    if igra_traje:
        return

    platno.delete("pobjeda_animacija")

    if eksplozija_kadrovi:
        kadar = eksplozija_kadrovi[frame_eksplozije % len(eksplozija_kadrovi)]
        platno.create_image(
            HIPO_X,
            HIPO_Y,
            image=kadar,
            tags="pobjeda_animacija"
        )
        frame_eksplozije += 1
        animacija_id = prozor.after(100, animiraj_eksploziju)
    else:

        platno.create_oval(
            HIPO_X - 120,
            HIPO_Y - 120,
            HIPO_X + 120,
            HIPO_Y + 120,
            fill="#ffcc00",
            outline="#ff6600",
            width=8,
            tags="pobjeda_animacija"
        )


def pobjedi():
    global igra_traje, pobjeda, gumb_igraj, proteklo_vrijeme, frame_eksplozije

    if not igra_traje:
        return

    igra_traje = False
    pobjeda = True
    frame_eksplozije = 0

    platno.delete("all")
    ukloni_gumbe()

    animiraj_eksploziju()

    platno.create_text(
        SIRINA // 2,
        VISINA // 2 - 80,
        text="HIPO JE EKSPLODIRAO!",
        fill="red",
        font=("Arial", 34, "bold")
    )

    platno.create_text(
        SIRINA // 2,
        VISINA // 2 - 25,
        text="POBJEDA!",
        fill="white",
        font=("Arial", 32, "bold")
    )

    platno.create_text(
        SIRINA // 2,
        VISINA // 2 + 25,
        text=f"VRIJEME: {int(proteklo_vrijeme)} s",
        fill="yellow",
        font=("Arial", 22, "bold")
    )

    gumb_igraj = Button(
        prozor,
        text="Igraj ponovno!",
        font=("Arial", 20, "bold"),
        bg="#4CAF50",
        fg="white",
        activebackground="#45a049",
        activeforeground="white",
        relief="raised",
        bd=5,
        command=pokreni_igru
    )
    platno.create_window(SIRINA // 2, VISINA // 2 + 115, window=gumb_igraj, width=260, height=55)


def izgubi():
    global igra_traje, proteklo_vrijeme, animacija_id

    if not igra_traje:
        return

    igra_traje = False
    
    if animacija_id is not None:
        prozor.after_cancel(animacija_id)
        animacija_id = None

    platno.delete("all")
    ukloni_gumbe()

    platno.create_text(
        SIRINA // 2,
        VISINA // 2 - 60,
        text="IZGUBIO SI!",
        fill="red",
        font=("Arial", 50, "bold")
    )

    platno.create_text(
        SIRINA // 2,
        VISINA // 2 + 5,
        text="Pogodila te prepreka.",
        fill="white",
        font=("Arial", 24)
    )

    platno.create_text(
        SIRINA // 2,
        VISINA // 2 + 45,
        text=f"VRIJEME: {int(proteklo_vrijeme)} s",
        fill="yellow",
        font=("Arial", 20, "bold")
    )

    global gumb_igraj
    gumb_igraj = Button(
        prozor,
        text="Igraj ponovno!",
        font=("Arial", 20, "bold"),
        bg="#4CAF50",
        fg="white",
        activebackground="#45a049",
        activeforeground="white",
        relief="raised",
        bd=5,
        command=pokreni_igru
    )
    platno.create_window(SIRINA // 2, VISINA // 2 + 120, window=gumb_igraj, width=260, height=55)


def pritisak_tipke(event):
    tipka = event.keysym.lower()
    pritisnute_tipke.add(tipka)

    if tipka == "space" and igra_traje:
        pucaj()


def pustanje_tipke(event):
    pritisnute_tipke.discard(event.keysym.lower())


def igra():
    global proteklo_vrijeme

    if not igra_traje or not igra_pokrenuta:
        return

    proteklo_vrijeme = time.time() - vrijeme_pocetka

    pomakni_hipo()
    pomakni_top()
    pomakni_voce()

    if not igra_traje:
        return

    pomakni_prepreke()
    provjeri_sudar()

    if not igra_traje:
        return

    platno.delete("igra_elementi")

    nacrtaj_hipo()
    nacrtaj_top()
    nacrtaj_voce()
    nacrtaj_prepreke()

    platno.create_text(
        SIRINA - 90,
        30,
        text=f"VRIJEME: {int(proteklo_vrijeme)} s",
        fill="white",
        font=("Arial", 16, "bold"),
        tags="igra_elementi"
    )

    prozor.after(1000 // FPS, igra)


def stvaraj_prepreke():
    if not igra_traje or not igra_pokrenuta:
        return

    stvori_prepreku()

    prozor.after(
        random.randint(700, 1400),
        stvaraj_prepreke
    )


def automatski_pucaj():
    if not igra_traje or not igra_pokrenuta:
        return

    pucaj()

    prozor.after(
        RAZMAK_AUTOMATSKOG_PUCANJA,
        automatski_pucaj
    )

prozor.bind_all("<KeyPress>", pritisak_tipke)
prozor.bind_all("<KeyRelease>", pustanje_tipke)
platno.bind("<Button-1>", pucaj)

prikazi_pocetni_ekran()

prozor.mainloop()
