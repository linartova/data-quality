//if (standard != "both") {
//    document.getElementById("view_dashboard").remove();
//}

function downloadGraphsFhirZIP() {
    window.location.href = '/download_graphs_fhir_zip';
}

function downloadFailuresFhirZIP() {
    window.location.href = '/download_failures_fhir_zip';
}

function pollSessionValue() {
    const intervalId = setInterval( () => {
        fetch('/check_failures_done_fhir')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                const done = data["response"];
                const tables = data["tables"];

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
    for (let i = 0; i < tables.length; i++) {
        const newDiv = document.createElement('div');
        newDiv.id = "table".concat("-", i.toString());
        newDiv.className = "table-container";
        newDiv.style.cssText = "height: 400px;";
        container.appendChild(newDiv);

        const tableJson = tables.at(i);
        const table = JSON.parse(tableJson);
        const plotData = table.data;
        const plotLayout = table.layout;
        Plotly.newPlot('table'.concat("-", i.toString()), plotData, plotLayout);
    }
}
window.onload = function() {
    pollSessionValue();
};