# Vulnb0x à la Feri

Egy olyan alkalmazás, mely megengedi, hogy különbözö github repository-k időnkénti felépítését és tesztelését konfiguráljuk, docker `Dockerfile`-ok segítségével.

## Támadási útvonal

- Felhasználó regisztrál
- Felhasználó belép
- Felhasználó konfigurál egy github repository, amely tartalmazza a támadás első részét [git repo](https://github.com/AlphaZoneR/attack-1):
    - A rendszer megengedi a volume-ok hozzácsatolását a konténerekhez, azzal az ötlettel, hogy úgyis csak lokális foldereket enged meg a docker: amennyiben relatív útvonalat adunk meg, mint például docker run -v ./thisdirectory/:/directory a következő error-t dobja "docker: Error response from daemon: create ./../../: "./../../" includes invalid characters for a local volume name, only "[a-zA-Z0-9][a-zA-Z0-9_.-]" are allowed. If you intended to pass a host directory, use absolute path."
    - A probléma az, hogy a így nem tudnánk relatív útvonalakat megadni, mégpedig ezt akarjuk, ezért a program mindig hozzáragassztja a felhasználó által megadott volume nevéhez a jelenlegi útvonalat.
    - Mivel intuitívan az első szabály szerint arra várnánk, hogy a docker ne engedje meg a mappában visszafelé történő navigálását, mint felhasználók a fenti folyamatot biztonságosnak tartjuk
    - A probléma az, hogy míg `./randomdirector:/\<mountpoint\>` helytelennek bizonyúl, `/home/<username>/../../:/<mountpoint>` nem az.
    - Ez megengedi a LFI(Local File Inclusion)-t, mely segítségével mountolhatjuk a lokális `/` foldert, majd innen `cat`-vel kiírhatjuk bizonyos fájlok tartalmát
- A felhasználó rátalál a `tree` parancs segítségével a jelenleg futó alkalmazás kódjára
- Kiderül, hogy az alkalmazás python-ban íródott, és [flask](https://flask.palletsprojects.com/en/2.0.x/)-et használ
- Flask-en belül használja a `flask.session` funkcionlalitást
- Flask a `session` információkat cookie-ban tárolja, melyeket elküld a kliensnek
- A cookie-k enkódolásához, egy titkot használ, melyet az alkalmazás `.env` fáljban tárol
- A felhasználó észreveszi, hogy az alkalmazás az adminisztrátor jogokat egy a `session`-on tárolt flag segítségével biztosítja
- A felhasználó, a megszerzett titok segítségével, módosítja a saját cookie-ját
```python
(pyenv) => import flask
(pyenv) => app = flask.Flask(__name__)
(pyenv) => app.secret_key = <acquired-secret-key>
(pyenv) => sessioni = flask.sessions.SecureCookieSessionInterface()
(pyenv) => serializer = sessioni.get_signing_serializer(app)
(pyenv) => serializer.dumps({"user": {"email": "<user_email>", "permissions": "admin"}})
```
- Firefox-ban Cookie Editor-val módosítja a session nevezetű cookie-t a fenti lépések segítségével kapott értékre
- Megjelenik egy új panel a kilensben, mely listázza az összes létező repository-t
- A felhasználó észreveszi, hogy még van egy repo, amely konfiurálva van, bob felhasználó által
- Az alkalmazás megengedi az egyszeri ssh privát kód konfigurálását, a klónozás érdekében
- Ezeket a kódokat a REST-api nem küldi vissza
- További elemzés után a felhasználó rájon, hogy az alkalmazás _docker in docker_ módban fut, és létezik egy MongoDB szerver is, melyben eltárolja az adatokat
- Egy újabb repository segítségével a felhasználó rácsatlakozik a MongoDB szerverre, és kinyeri a konfigurált repositorykat.
- Az így kinyert privát kulccsal megpróbál rácsatlakozni a szerverre ssh-val, és sikerül. Kiderül, hogy bob root jogosultsággal rendelkezik.  

## Javítási lehetőségek
### LFI kijavítása

Mivel a mountpontok meghatározása egy fontos funkcionalitása a programnak, fontos kijavítani ezt úgy, hogy felhasználható maradjon továbbá is. A legegyszerűbb megoldás a lokális fájlendszerhez megadott mountpont validálása. Mivel az egyetlen megengedett útvonal, a repository-n belül kell elhelyezkedjen, végezhetünk egy ellenőrzést, hogy a teljesen kiértékelt útvonal benne legyen a jelenlegi repository mappájában. Ezzel a lépéssel kizárjuk azt, hogy az alkalmazás felhasználója valaha is rájöjjön a flask-ben használt titokra, vagy akármilyen más nem megengedett LFI-t végezzen. Amennyiben biztosítani tudjuk azt, hogy ez a titok soha nem kerül publikussá, a fentebb meghatározott támadási útvonal már nem használható. Ennek ellenére, fontos, hogy több szinten is levédjük az alkalmazásunkat. A következő probléma a JWT token módosítása volt.

### JWT cookie manipulation kijavítása 
