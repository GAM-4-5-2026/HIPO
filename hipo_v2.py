
import tkinter as tk
import random
import math
from pathlib import Path



SIRINA, VISINA = 1000, 700
FPS = 30

HIPO_X, HIPO_Y = SIRINA // 2, 120
HIPO_POCETNA_VELICINA = 130
HIPO_MAX_VELICINA = 500
HIPO_RAST_PO_HITCU = 20

TOP_BRZINA = 7
VOCE_BRZINA = 10
RAZMAK_AUTOMATSKOG_PUCANJA = 500

BASE_DIR = Path(__file__).resolve().parent

try:
    from PIL import Image, ImageTk
    PIL_DOSTUPAN = True
except ImportError:
    PIL_DOSTUPAN = False


prozor = tk.Tk()
prozor.title("Hipo Space Shooter")
prozor.resizable(False, False)

platno = tk.Canvas(
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
        return tk.PhotoImage(file=str(putanja(naziv)))
    except tk.TclError:
        print(f"Upozorenje: ne mogu učitati {naziv}.")
        return None


# Učitavanje slika
hipo_original = ucitaj_tk_sliku("mali.png")
jabuka_original = ucitaj_tk_sliku("jabuka.png")
lubenica_original = ucitaj_tk_sliku("lubenica.png")


# Učitavanje animacije topa
top_kadrovi = []

try:
    gif = tk.PhotoImage(file=str(putanja("cannon.gif")))
    indeks = 0

    while True:
        try:
            kadar = tk.PhotoImage(
                file=str(putanja("cannon.gif")),
                format=f"gif -index {indeks}"
            )
            top_kadrovi.append(kadar)
            indeks += 1
        except tk.TclError:
            break

    if not top_kadrovi:
        top_kadrovi = [gif]

except tk.TclError:
    print("Upozorenje: ne mogu učitati cannon.gif.")


def tk_slika_velicine(original, sirina, visina):
    if original is None:
        return None

    sirina = max(1, int(sirina))
    visina = max(1, int(visina))

    # Rezervno skaliranje ako Pillow nije instaliran.
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
hipo_velicina = HIPO_POCETNA_VELICINA
hipo_prikaz = None
hipo_prikaz_velicina = None

top_x, top_y = SIRINA // 2, VISINA - 100

pritisnute_tipke = set()
voce = []
prepreke = []

igra_traje = True
pobjeda = False
frame_topa = 0


# Učitavanje i skaliranje voća
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
                        (36, 36),
                        Image.Resampling.LANCZOS
                    )
                    slike_voca[naziv] = ImageTk.PhotoImage(im)
            except Exception:
                slike_voca[naziv] = original
        else:
            slike_voca[naziv] = original


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

    # Rezervni prikaz ako slika nije dostupna
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
            top_x - 25,
            top_y - 15,
            top_x + 25,
            top_y + 15,
            fill="#555555",
            outline="black",
            tags="top"
        )

        platno.create_rectangle(
            top_x - 7,
            top_y - 35,
            top_x + 7,
            top_y - 10,
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
        "y": top_y - 35,
        "tip": tip,
        "brzina": VOCE_BRZINA,
        "velicina": 18,
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
                style=tk.ARC,
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

    top_x = max(35, min(SIRINA - 35, top_x))
    top_y = max(VISINA // 2, min(VISINA - 45, top_y))


def pomakni_voce():
    global hipo_velicina, hipo_prikaz_velicina

    for v in voce[:]:
        v["y"] -= v["brzina"]

        # Sudar voća s preprekama
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

        # Hitbox prati veličinu Hipove slike.
        # Margina je 5 % sa svake strane.
        margina = hipo_velicina * 0.05

        lijevo = HIPO_X - hipo_velicina / 2 + margina
        desno = HIPO_X + hipo_velicina / 2 - margina
        gore = HIPO_Y - hipo_velicina / 2 + margina
        dolje = HIPO_Y + hipo_velicina / 2 - margina

        najblizi_x = max(
            lijevo,
            min(v["x"], desno)
        )
        najblizi_y = max(
            gore,
            min(v["y"], dolje)
        )

        dodiruje_hipa = math.hypot(
            v["x"] - najblizi_x,
            v["y"] - najblizi_y
        ) <= v["velicina"]

        if dodiruje_hipa:
            stara_velicina = hipo_velicina

            hipo_velicina = min(
                HIPO_MAX_VELICINA,
                hipo_velicina + HIPO_RAST_PO_HITCU
            )

            # Ponovno skaliraj sliku nakon rasta.
            if hipo_velicina != stara_velicina:
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
        # Prilagođen hitbox topa: Hipo nije uključen u ovaj sudar.
        if math.hypot(
            top_x - p["x"],
            top_y - p["y"]
        ) < 28 + p["velicina"] * 0.65:
            izgubi()
            return


def pobjedi():
    global igra_traje, pobjeda

    if not igra_traje:
        return

    igra_traje = False
    pobjeda = True

    platno.delete("all")

    platno.create_oval(
        HIPO_X - 210,
        HIPO_Y - 150,
        HIPO_X + 210,
        HIPO_Y + 150,
        fill="#ffcc00",
        outline="#ff6600",
        width=10
    )

    platno.create_text(
        SIRINA // 2,
        VISINA // 2,
        text="HIPO JE EKSPLODIRAO!",
        fill="red",
        font=("Arial", 34, "bold")
    )

    platno.create_text(
        SIRINA // 2,
        VISINA // 2 + 60,
        text="POBJEDA!",
        fill="white",
        font=("Arial", 32, "bold")
    )


def izgubi():
    global igra_traje

    if not igra_traje:
        return

    igra_traje = False
    platno.delete("all")

    platno.create_text(
        SIRINA // 2,
        VISINA // 2,
        text="IZGUBIO SI!",
        fill="red",
        font=("Arial", 50, "bold")
    )

    platno.create_text(
        SIRINA // 2,
        VISINA // 2 + 65,
        text="Pogodila te prepreka.",
        fill="white",
        font=("Arial", 24)
    )


def pritisak_tipke(event):
    tipka = event.keysym.lower()
    pritisnute_tipke.add(tipka)

    if tipka == "space":
        pucaj()


def pustanje_tipke(event):
    pritisnute_tipke.discard(event.keysym.lower())


def igra():
    if not igra_traje:
        return

    pomakni_top()
    pomakni_voce()

    if not igra_traje:
        return

    pomakni_prepreke()
    provjeri_sudar()

    if not igra_traje:
        return

    nacrtaj_hipo()
    nacrtaj_top()
    nacrtaj_voce()
    nacrtaj_prepreke()

    prozor.after(1000 // FPS, igra)


def stvaraj_prepreke():
    if not igra_traje:
        return

    stvori_prepreku()

    prozor.after(
        random.randint(700, 1400),
        stvaraj_prepreke
    )


def automatski_pucaj():
    if not igra_traje:
        return

    pucaj()

    prozor.after(
        RAZMAK_AUTOMATSKOG_PUCANJA,
        automatski_pucaj
    )


# Kontrole
prozor.bind_all("<KeyPress>", pritisak_tipke)
prozor.bind_all("<KeyRelease>", pustanje_tipke)
platno.bind("<Button-1>", pucaj)

# Pokretanje igre
nacrtaj_hipo()
nacrtaj_top()
stvaraj_prepreke()
automatski_pucaj()
igra()

prozor.mainloop()
