document.addEventListener('DOMContentLoaded', function () {
    const datiSala = document.getElementById('datiSala');
    const postiPerFila = JSON.parse(datiSala.dataset.postiPerFila);
    const postiOccupati = new Set(JSON.parse(datiSala.dataset.postiOccupati));

    const filaCentrale = Math.floor(postiPerFila.length / 2);
    const salaContainer = document.getElementById('sala-container');
    let selectedPosti = [];
    let counter = 1;

    const schermo = document.createElement('div');
    schermo.className = 'text-center text-white bg-secondary py-2 rounded mb-4';
    schermo.innerText = '🟦 SCHERMO';
    salaContainer.appendChild(schermo);

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
            btn.innerText = counter;
            btn.dataset.posto = counter;
            btn.dataset.isGold = (i === filaCentrale).toString();

            if (postiOccupati.has(counter)) {
                btn.classList.add('btn-danger');
                btn.disabled = true;
                btn.title = 'Posto occupato';
            } else if (i === filaCentrale) {
                btn.classList.add('btn-warning');
                btn.title = 'Fila centrale (Gold)';
            } else {
                btn.classList.add('btn-info');
                btn.title = 'Posto disponibile';
            }

            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const posto = parseInt(btn.dataset.posto);

                if (selectedPosti.includes(posto)) {
                    selectedPosti = selectedPosti.filter(p => p !== posto);
                    btn.classList.remove('btn-success');
                    btn.classList.add(btn.dataset.isGold === "true" ? 'btn-warning' : 'btn-info');
                } else {
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

    document.getElementById('prenotazione-form').addEventListener('submit', function(e) {
        if (!areContiguous(selectedPosti)) {
            e.preventDefault();
            alert("Puoi selezionare solo posti contigui!");
            return;
        }

        document.getElementById('posti-input').value = JSON.stringify(selectedPosti);
    });

    function areContiguous(array) {
        if (array.length <= 1) return true;
        array.sort((a, b) => a - b);
        for (let i = 1; i < array.length; i++) {
            if (array[i] !== array[i - 1] + 1) return false;
        }
        return true;
    }
});
