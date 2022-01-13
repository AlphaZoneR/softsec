# Vulnb0x à la Feri

Egy olyan alkalmazás, mely megengedi, hogy különbözö github repository-k időnkénti felépítését és tesztelését konfiguráljuk, docker segítségével.

## Támadási útvonal

- Felhasználó regisztrál
- Felhasználó belép
- Felhasználó konfigurál egy github repository, amely tartalmazza a támadás első részét:
    - A rendszer megengedi a volume-ok hozzácsatolását a konténerekhez, azzal az ötlettel, hogy úgyis csak lokális foldereket enged meg a docker: amennyiben relatív útvonalat adunk meg, mint például docker run -v ./thisdirectory/:/directory a következő error-t dobja "docker: Error response from daemon: create ./../../: "./../../" includes invalid characters for a local volume name, only "[a-zA-Z0-9][a-zA-Z0-9_.-]" are allowed. If you intended to pass a host directory, use absolute path."
    - A probléma az, hogy a így nem tudnánk relatív útvonalakat megadni, mégpedig ezt akarjuk, ezért a program mindig hozzáragassztja a felhasználó által megadott volume nevéhez a jelenlegi útvonalat.
    - Mivel intuitívan az első szabály szerint arra várnánk, hogy a docker ne engedje meg a mappában visszafelé történő navigálását, mint felhasználók a fenti folyamatot biztonságosnak tartjuk
    - A probléma az, hogy míg `./randomdirector:/\<mountpoint\>` helytelennek bizonyúl, `/home/<username>/../../:/<mountpoint>` nem az.
    - Ez megengedi a LFI(Local File Inclusion)-t, mely segítségével mountolhatjuk a lokális `/` foldert, majd innen `cat`-vel kiírhatjuk bizonyos fájlok tartalmát
- A felhasználó rátalál a `tree` parancs segítségével a jelenleg futó alkalmazás kódjára
- Kiderül, hogy az alkalmazás python-ban íródott, és flask-et használ
- Flask-en belül használja a `session` funkcionlalitást
- Flask a `session` információkat cookie-ban tárolja, melyeket elküld a kliensnek
- A cookie-k enkódolásához, egy titkot használ, melyet az alkalmazás `.env` fáljban tárol
- A felhasználó észreveszi, hogy az alkalmazás az adminisztrátor jogokat egy a `session`-on tárolt flag segítségével biztosítja
- A felhasználó, a megszerzett titok segítségével, módosítja a saját cookie-ját
    - Megnyit egy `python` ablakot
    - `import flask.sessions.SecureCookieSessionInterface`
    - `import flask`
    - `app = flask.Flask(__name__)`
    - `app.secret_key = <acquired-secret-key>`
    - `sessioni = flask.sessions.SecureCookieSessionInterface()`
    - `serializer = sessioni.get_signing_serializer(app)`
    - `serializer.dumps({"user": {"email": "<user_email>", "permissions": "admin"}})`
    - Firefox-ban Cookie Editor-val módosítja a `session` nevezetű cookie-t a fenti lépések segítségével kapott értékre

- Megjelenik egy új panel a kilensben, mely listázza az összes létező repository-t
- A felhasználó észreveszi, hogy még van egy repo, amely konfiurálva van, bob felhasználó által
- Az alkalmazás megengedi az egyszeri ssh privát kód konfigurálását, a klónozás érdekében
- Ezeket a kódokat a REST-api nem küldi vissza
- További elemzés után a felhasználó rájon, hogy az alkalmazás _docker in docker_ módban fut, és létezik egy MongoDB szerver is, melyben eltárolja az adatokat
- Egy újabb repository segítségével a felhasználó rácsatlakozik a MongoDB szerverre, és kinyeri a konfigurált repositorykat.
- Az így kinyert privát kulccsal megpróbál rácsatlakozni a szerverre ssh-val, és sikerül. Kiderül, hogy bob root jogosultsággal rendelkezik.  

## Javítási lehetőségek

- 