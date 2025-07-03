/*      LO script si occupa di renderare dinamente la "sala" leggendo il layout da "postiPerFila"
        creando per ogni posto un bottone, e generando la lista di posti al loro "onClick"
*/

document.addEventListener('DOMContentLoaded', function () {
    // Ottengo prima di tutto i dati "postiPerFila e postiOccupati" da un widget messo appositamente
    // in proiezione_detail
    const datiSala = document.getElementById('datiSala');
    const postiPerFila = JSON.parse(datiSala.dataset.postiPerFila);
    const postiOccupati = new Set(JSON.parse(datiSala.dataset.postiOccupati));

    const filaCentrale = Math.floor(postiPerFila.length / 2);
    const salaContainer = document.getElementById('sala-container');
    let selectedPosti = [];
    let counter = 1;

    // Metto il widget html per mostrare lo schermo
    const schermo = document.createElement('div');
    schermo.className = 'text-center text-white bg-secondary py-2 rounded mb-4';
    schermo.innerText = '🟦 SCHERMO';
    salaContainer.appendChild(schermo);

    // Itero sulla lista "postiPerFila"   [10,10,15] es  (numPosti,i) sarebbe "enumerate"
    postiPerFila.forEach((numPosti, i) => {
        const filaDiv = document.createElement('div');
        filaDiv.className = 'd-flex justify-content-center mb-3 align-items-center gap-2';

        const label = document.createElement('div');
        label.className = 'text-white me-2 fw-bold';
        label.innerText = String.fromCharCode(65 + i);
        filaDiv.appendChild(label);

        for (let j = 0; j < numPosti; j++) {
            const btn = document.createElement('button');
            btn.className = 'btn btn-sm rounded-pill px-3 fw-semibold seat-btn';
            btn.innerText = counter;    //Il counter tiene conto dei posti incrementalmente
            btn.dataset.posto = counter;
            btn.dataset.isGold = (i === filaCentrale).toString();

            if (postiOccupati.has(counter)) {   //Disabilito il bottone se posto occupato (e metto rosso)
                btn.classList.add('btn-danger');
                btn.disabled = true;
                btn.title = 'Posto occupato';
            } else if (i === filaCentrale) { // Se la fila (i) è quella centrale metto il posto gold
                btn.classList.add('btn-warning');
                btn.title = 'Fila centrale (Gold)';
            } else {                        //Altrimenti è blu
                btn.classList.add('btn-info');
                btn.title = 'Posto disponibile';
            }

            //Ad ogni bottone do l'evento "onClick",
            //  in cui metto il posto (btn.dataset.posto) in selectedPosti (lista) e coloro il btn di verde
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const posto = parseInt(btn.dataset.posto);

                if (selectedPosti.includes(posto)) {    // se era già selezionato lo deselezione togliendolo dalla lista
                    selectedPosti = selectedPosti.filter(p => p !== posto);
                    btn.classList.remove('btn-success');
                    btn.classList.add(btn.dataset.isGold === "true" ? 'btn-warning' : 'btn-info');
                } else {        // Qui invece lo seleziono
                    selectedPosti.push(posto);
                    btn.classList.remove('btn-info', 'btn-warning');
                    btn.classList.add('btn-success');
                }
            });

            filaDiv.appendChild(btn);
            counter++;
        }

        salaContainer.appendChild(filaDiv);
    });

    //Per un controllo lato client
    document.getElementById('prenotazione-form').addEventListener('submit', function(e) {
        if (!areContiguous(selectedPosti)) {
            e.preventDefault();
            alert("Puoi selezionare solo posti contigui!");
            return;
        }

        document.getElementById('posti-input').value = JSON.stringify(selectedPosti);
    });

    //Controlla se il vettore "selectedPosti" abbia posti contigui
    function areContiguous(array) {
        if (array.length <= 1) return true;
        array.sort((a, b) => a - b);
        for (let i = 1; i < array.length; i++) {
            if (array[i] !== array[i - 1] + 1) return false;
        }
        return true;
    }
});
