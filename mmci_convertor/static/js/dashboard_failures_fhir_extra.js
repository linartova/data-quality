function downloadGraphsFhirZIP() {
    window.location.href = '/download_graphs_fhir_zip_extra';
}

function downloadFailuresFhirZIP() {
    window.location.href = '/download_failures_fhir_zip_extra';
}

function pollSessionValue() {
    const intervalId = setInterval( () => {
        fetch('/check_failures_done_fhir_extra')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                const done = data["response"];
                const tables = data["tables"];

                const count = tables.length;
                console.log(count);

                if (done == true) {
                    addNewDiv(tables);
                    clearInterval(intervalId);
                }
                console.log(done);
            })
            .catch(error => console.error('Error:', error));
    }, 1000);
}

function addNewDiv(tables) {
    const container = document.getElementById("main-content");
    const progressBar = document.getElementById("progress-bar");
    if (progressBar != null) {
        progressBar.style.cssText = "display: none;";
        }
    for (let i = 0; i < tables.length; i++) {
        const newDiv = document.createElement('div');
        const newDivId = "table".concat("-", i.toString());
        newDiv.id = newDivId;
        newDiv.className = "table-container";
        newDiv.style.cssText = "height: 400px;";
        container.appendChild(newDiv);

        const tableHTML = tables.at(i);
        document.getElementById(newDivId).innerHTML = tableHTML;

    }
}
window.onload = function() {
    pollSessionValue();
};