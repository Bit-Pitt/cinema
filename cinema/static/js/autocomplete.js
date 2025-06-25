
document.addEventListener("DOMContentLoaded", function () {
    const fields = ["titolo", "genere"];

    fields.forEach(function (fieldId) {
        const input = document.getElementById(fieldId);
        input.autocomplete = "off";

        // Creo il contenitore dropdown (vuoto e nascosto)   [quello che conterrà i "suggeriti"]
        const dropdown = document.createElement("div");
        dropdown.className = "autocomplete-dropdown list-group position-absolute w-100";
        dropdown.style.zIndex = 1000;
        dropdown.style.top = "100%";
        dropdown.style.left = 0;
        dropdown.style.display = "none";
        dropdown.style.maxHeight = "200px";
        dropdown.style.overflowY = "auto";
        dropdown.style.backgroundColor = "#212529"; // scuro come bootstrap dark

        // Posiziono relativo al contenitore del campo (per absolute positioning)
        input.parentNode.style.position = "relative";
        input.parentNode.appendChild(dropdown);

        //ad ogni tasto premuto chiamo questa funzione, se lenght >2 chiamerà una view per ottenere
        // tramite json i possibili risultati (max 5), per ognuno crea un elemento da mettere al 
        // menu (appendChild) [al dropdown==menu] , che se cliccato setta la label con il suo valore
        input.onkeyup = function () {
            const s = input.value.trim();
            if (s.length < 2) {
                dropdown.style.display = "none";
                return;
            }

            const xhttp = new XMLHttpRequest();
            xhttp.onload = function () {
                if (xhttp.status === 200) {
                    try {
                        const data = JSON.parse(xhttp.responseText);
                        if (data.results && data.results.length > 0) {
                            dropdown.innerHTML = "";  // pulisco dropdown

                            data.results.forEach(item => {
                                const elem = document.createElement("a");
                                elem.className = "list-group-item list-group-item-action bg-dark text-white";
                                elem.textContent = item;
                                elem.style.cursor = "pointer";

                                elem.onclick = function () {
                                    input.value = item;
                                    dropdown.style.display = "none";
                                };

                                dropdown.appendChild(elem);
                            });

                            dropdown.style.display = "block";
                        } else {
                            dropdown.style.display = "none";
                        }
                    } catch (e) {
                        console.error("Risposta non valida:", e);
                        dropdown.style.display = "none";
                    }
                } else {
                    dropdown.style.display = "none";
                }
            };

            xhttp.open("GET", `/films/autocomplete/?w=${fieldId}&q=${encodeURIComponent(s)}`, true);
            xhttp.send();
        };

        // Chiudo dropdown se clicco fuori dall’input e dropdown
        document.addEventListener("click", function (e) {
            if (e.target !== input && !dropdown.contains(e.target)) {
                dropdown.style.display = "none";
            }
        });
    });
});

 
/*          VERSIONE precedente funzionante con implementazione simile Lezione!
document.addEventListener("DOMContentLoaded", function () {
    const fields = ["titolo", "genere"];


    //per ogni stringa in "fields" prende l'elemento (widget), assegna la fun onkeyup
    fields.forEach(function (fieldId) {
        const input = document.getElementById(fieldId);
        input.autocomplete = "off";

        input.onkeyup = function () {
            const s = input.value.trim();
            if (s.length < 3) return;

            const xhttp = new XMLHttpRequest();
                //quando ce un cambio di stato (arriva risposta):
            xhttp.onload = function () {
                if (xhttp.status === 200) {
                    try {
                        const data = JSON.parse(xhttp.responseText);    //autocomplete restituisce un json
                        if (data.results && data.results.length === 1) {
                            input.value = data.results[0];
                        }
                    } catch (e) {
                        console.error("Risposta non valida:", e);
                    }
                }
            };

            //compongo la chiamata a "autocomplete",    "encode .. per robustezza"
            xhttp.open("GET", `/films/autocomplete/?w=${fieldId}&q=${encodeURIComponent(s)}`, true);
            xhttp.send();
        };
    });
});
*/