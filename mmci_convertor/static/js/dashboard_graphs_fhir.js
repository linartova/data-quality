function downloadGraphsFhirZIP() {
    window.location.href = '/download_graphs_fhir_zip';
}

function downloadFailuresFhirZIP() {
    window.location.href = '/download_failures_fhir_zip';
}

function pollSessionValue() {
    const intervalId = setInterval(() => {
        fetch('/check_graphs_done_fhir')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                const done = data["response"];
                const graphs = data["graphs"];

                const count = graphs.length;
                addProgressBar(count);

                if (done == true) {
                    addNewDiv(graphs);
                    clearInterval(intervalId);
                }
                console.log(done);
            })
            .catch(error => console.error('Error:', error));
    }, 1000);
}

function addProgressBar(count) {
    const progressBar = document.getElementById("progress-bar");
    progressBar.textContent = count.toString().concat(" out of 16 graphs finished. Please wait.")
}

function addNewDiv(graphs) {
    const container = document.getElementById("main-content");
    const progressBar = document.getElementById("progress-bar");
    progressBar.style.cssText = "display: none;";
    for (let i = 0; i < graphs.length; i++) {
        const newDiv = document.createElement('div');
        newDiv.id = "graph".concat("-", i.toString());
        newDiv.className = "graph-container";
        newDiv.style.cssText = "height: 400px;";
        container.appendChild(newDiv);

        const graphJson = graphs.at(i);
        const graph = JSON.parse(graphJson);
        const plotData = graph.data;
        const plotLayout = graph.layout;
        Plotly.newPlot('graph'.concat("-", i.toString()), plotData, plotLayout);
    }
}
window.onload = function() {
    pollSessionValue();
};