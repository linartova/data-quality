function filterContent() {
    const query = document.getElementById("search-bar").value.toLowerCase();
    const contentItems = document.querySelectorAll(".content-item");

    for (let i = 0; i < contentItems.length; i++) {
        const contentText = contentItems[i].innerText.toLowerCase();
        if (contentText.includes(query)) {
            document.getElementById((i + 1).toString()).style.display = "block";
        } else {
            document.getElementById((i + 1).toString()).style.display = "none";
        }
    }
}