# Botnet attacks 2021 - Feri

## Mozi 
- P2P botnet, mely 2019-ben ütötte fel a fejét
- Jellemzően IoT eszközöket támadott, melyek gyenge telnet jelszavakkal rendelkeztek
- 2021-ben kb. 1,5 mió fertőzött nódust esztimálnak
- DHT (distributed hash table) használ, így szinkronizálja az adatokat a nódusok között
- Milvel P2P, nehéz kiégetni
- Míg álltólagos szerzőjét elkapták, 2021-ben egy új verzió virágzott ki: nem csak IoT eszközöket, hanem Netgear, Huawey és ZTE routereket is, melyeken perszisztens is marad.
- CVE-2015-1328 - overlayfs LK 3.19.0-21.21 előtt nem ellenőrzi helyesen a hozzáférési jogokat a felső fájlrendszer könyvtárban, konfigurációs fáljokat módosít, elmenti magát
-   /etc/rc.d
    /etc/init.d
- CVE-2014-2321 - zte ZTE F460 and F660  kábelmodemek lehetővé teszik a távoli támadók számára, hogy adminisztrátori hozzáférést kapjanak  sendcmd kéréseken keresztüul

## Emotet

- Európában figyeltek fel rá először 2014-ben
- 2017-ben megtámadta az Észak-Karolina iskolai körzetet
- Mailek csatolmányában, illetve fertőzött linkeken keresztül terjedt
- Loader tipusú botnet, mely megtámad klienseket, majd ezek kombinált számítástechnikai erejét pénzért árulja (loader ... bármit fel lehet installálni) 
- 2021-ben sikerült az FBI-nak csoportosúlnia némely magánszervezetekkel, melyek segítségével a legalsó szintű layereket úgy módosították, hogy a rá csatlakozó kliensek az FBI infrastruktúrájához csatlakozzanak

