
#La funzione si aspetta la stringa "genere" del modello "Film"  Es:  "Thriller / Drama"
def collega_film_immagine(genere):
    generi_immagini = {
            "animazione": "animazione.jpg",
            "azione": "azione.jpg",
            "avventura":"azione.jpg",
            "crime": "crime.jpg",
            "drammatico": "drammatico.jpg",
            "fantasy": "fantasy.jpg",
            "fantascienza": "fantasy.jpg",
            "thriller": "thriller.jpg",
            "biografico": "biografia.jpg",
        }

    genere = genere.lower()
    # I generi possono essere due nella forma  "Thriller / drama" ==> voglio ['thriller','drama']
    generi_film = [g.strip() for g in genere.split("/")]

    # Vista la massiccia presenza di "drammatici" e quindi la relativa immagine, posiziono il genere
    # in seconda posizione così da ridurne l'occorrenza
    if len(generi_film) > 1 and generi_film[0] == "drammatico":
        generi_film[0], generi_film[1] = generi_film[1], generi_film[0]

    immagine = "default.jpg"
    for g in generi_film:
        if g in generi_immagini:
            immagine = generi_immagini[g]           #assegno la jpg specifica
            return immagine
    
    return "default.jpg"

