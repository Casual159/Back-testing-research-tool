

> Interní zápis z konverzace s AI shrnující záměr, hranice a charakteristiky produktu

---

## **1. Záměr produktu (WHY)**



Produkt je **research a analytický nástroj** určený k:

- systematickému zkoumání tržního chování,

- formulaci obchodních hypotéz,

- návrhu a testování algoritmických strategií,

- validaci strategií v historickém a simulovaném prostředí.




**Primární cíl:**



> Pomoci uživateli porozumět chování strategie, nikoli ji automaticky provozovat za něj.



Produkt **není**:

- investiční poradenství,

- trading bot,

- služba správy kapitálu,

- live trading platforma.


---

## **2. Funkční rozsah (WHAT)**



### **A) Backtesting**

- práce s historickými tržními daty,

- generování hypotéz, situací a strategií,

- dávkové (batch) backtesty,

- statistická a behaviorální interpretace výsledků.




### **B) Simulované „live“ chování (paper / testnet)**

- simulované provádění obchodních příkazů,

- připojení **výhradně k testnetům burz** (např. Binance testnet),

- žádné reálné prostředky, žádná finanční hodnota,

- časově omezené běhy (např. 7 dní),

- slouží k pozorování chování strategie v kvazi‑reálném čase.




### **C) Export strategie**

- export logiky strategie (pravidla, parametry),

- formáty: pseudokód, Python, Pine, JSON apod.,

- strategie jsou určeny k **samostatnému použití uživatelem mimo platformu**.


---

## **3. Explicitní omezení (WHAT THE PRODUCT DOES NOT DO)**



Produkt:

- neprovádí reálné obchody,

- nepřistupuje k live účtům uživatelů,

- neuchovává live API klíče,

- nenasazuje strategie na burzu,

- nepřebírá odpovědnost za finanční výsledky.


---

## **4. Technické hranice (HOW)**

- backend-first SaaS architektura,

- žádné live trading endpointy,

- testnet připojení:

    - technicky hardcoded,

    - nelze přepnout na live prostředí,


- veškeré exekuce jsou simulované.




> Architektura záměrně znemožňuje nechtěné nebo skryté live obchodování.

---

## **5. Odpovědnosti**



### **Platforma**

- poskytuje analytické a simulační nástroje,

- provádí výpočty a simulace,

- vizualizuje výsledky.




### **Uživatel**

- interpretuje výstupy,

- rozhoduje o použití strategií,

- případné nasazení strategie provádí **zcela mimo platformu** a na vlastní odpovědnost.


---

## **6. Právní a regulační pozice**

- produkt je **software / analytický nástroj**,

- nejde o investiční službu dle regulací (ČNB / MiFID),

- platforma:

    - nedrží cizí prostředky,

    - neprovádí obchody,

    - neposkytuje investiční doporučení.





**Důsledek:**

- není vyžadována licence,

- není vyžadována kapitálová jistina,

- nejsou aplikovány AML povinnosti nad rámec běžného SaaS.


---

## **7. Monetizační model**

- subscription SaaS,

- cenové plány dle:

    - výpočetního objemu,

    - počtu backtestů,

    - délky simulací,


- AI náklady:

    - limity v tarifu,

    - možnost dokoupení nadlimitního usage.





> Žádný revenue share, žádná vazba na výkonnost tradingu.

---

## **8. Zkušenost uživatele, onboarding a “wow efekt”**



Produkt se **vědomě neprofiluje jako nástroj pro rychlý zisk** ani jako predátorský money-grab. Zároveň si ale klade za cíl poskytovat **silný “wow efekt”**, který uživateli během krátké, ale soustředěné interakce ukáže skutečný potenciál platformy.



### **Onboarding & tutorial**

- nový uživatel je proveden **strukturovaným tutoriálem**,

- tutorial demonstruje klíčové schopnosti produktu:

    - formulaci hypotézy,

    - automatizované sestavení testů,

    - běh backtestů / simulací,

    - interpretaci výsledků pomocí AI,


- cílem je, aby uživatel během **cca 30 minut informovaného soustředění**:

    - pochopil principy nástroje,

    - zažil konkrétní přínos,

    - viděl reálný potenciál dalšího zkoumání.





### **AI jako průvodce poznáním**

- AI v produktu nefunguje jen jako generátor,

- AI:

    - navrhuje relevantní testy,

    - provádí jejich vyhodnocení,

    - **interpretuje výsledky v kontextu uživatelova záměru**,

    - komentuje získané poznání a upozorňuje na vzorce, limity a rizika.





> Klíčovým výstupem není “výdělek”, ale **relevantní poznání**, které má pro uživatele praktickou hodnotu.



### **Gamifikace**

- produkt obsahuje **lehké prvky gamifikace**, např.:

    - postupné odemykání možností,

    - výzvy / experimenty,

    - vizualizace pokroku v porozumění strategiím,


- gamifikace slouží k:

    - zvýšení angažovanosti,

    - udržení pozornosti,

    - motivaci k hlubšímu zkoumání.





### **Cílové skupiny**

- pokročilí tradeři a analytici (primární cílovka),

- technicky zvídaví uživatelé,

- **mladší generace**, které chtějí:

    - pochopit trading,

    - experimentovat bezpečnou formou,

    - připravit se bez rizika reálných ztrát.





Produkt je navržen tak, aby byl:

- bezpečný pro začátečníky,

- dostatečně hluboký pro experty.


---

## **9. Komunikační a marketingový rámec**



Používaný jazyk:

- research

- simulation

- hypothesis testing

- strategy exploration




Nepoužívaný jazyk:

- „automatický zisk”,

- „obchoduje za vás”,

- „garantovaný výnos”.


---

## **9. Severní bod produktu (one‑liner)**



> **Analytický a simulační nástroj pro návrh a pochopení obchodních strategií, nikoli pro jejich automatické provozování s reálnými penězi.**

---

_Dokument slouží jako interní produktový rámec a výchozí bod pro ToS, marketing i technickou architekturu._



**Komentář:**
Do dokumentu jsem **adresně doplnil novou kapitolu o uživatelské zkušenosti, onboardingu, wow efektu, roli AI a gamifikaci** – a zároveň jsem **nezměnil původní záměr ani právní hranice produktu**.



Teď ten dokument říká jasně tři důležité věci najednou:

1. **Neprodáváš rychlý zisk ani iluze**

    – je tam explicitně vymezený anti-predátorský postoj.

2. **Přesto chceš silný první zážitek**

    – 30 minut soustředění = „aha moment“, kdy uživatel:

    - něco _pochopí_,

    - něco _uvidí na datech_,

    - něco _si odnese_.


3. **AI je kurátor poznání, ne hype generátor**

    – vede, testuje, interpretuje, komentuje.

    To je velmi dospělá a odlišující pozice oproti „AI trading bot“ scéně.




Z produktového hlediska je tohle **výborně vyvážené**:

- silné pro marketing,

- obhajitelné právně,

- atraktivní i pro mladší generaci,

- ale pořád respektované profíky.




Až budeš chtít další krok, dává smysl:

- převést tu onboarding část do **konkrétní user journey (krok 1–10)**,

- nebo navrhnout **„wow demo scénář“**, který se bude opakovat u každého nového uživatele,

- případně z toho udělat **landing-page narrative**.




Řekni, kam chceš jít dál – ten základ je teď velmi pevný.
