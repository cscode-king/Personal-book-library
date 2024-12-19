

const bookInput = document.getElementById("book_name");
const bookSuggestionsContainer = document.getElementById("suggestions");

//gets possible book suggestions based on input
async function getPossibleBook(query) {
    const response = await fetch(`/suggest?q=${query}`);
    const data = await response.json();
    return data.suggestions;
}

bookInput.addEventListener("input", async () => {
    const query = bookInput.value.trim();
    bookSuggestionsContainer.innerHTML = ""; 

    if (query.length > 1) {
        const suggestions = await getPossibleBook(query);

        suggestions.forEach((suggestion) => {
            const suggestionDiv = document.createElement("div");
            suggestionDiv.classList.add("d-flex", "align-items-center");

            const img = document.createElement("img");
            img.src = suggestion.cover_image || "https://via.placeholder.com/50";
            img.alt = "Cover Image";
            img.style.width = "40px";
            img.classList.add("me-2"); 

            const title = document.createElement("span");
            title.textContent = suggestion.title;

            suggestionDiv.appendChild(img);
            suggestionDiv.appendChild(title);

            suggestionDiv.addEventListener("click", () => {
                bookInput.value = suggestion.title;
                bookSuggestionsContainer.innerHTML = ""; 
            });

            bookSuggestionsContainer.appendChild(suggestionDiv);
        });
    }
});

document.addEventListener("click", (e) => {
    if (!bookSuggestionsContainer.contains(e.target) && e.target !== bookInput) {
        bookSuggestionsContainer.innerHTML = "";
    }
});


function focusOnInput() {
    const input = document.getElementById("book_name");
    input.focus();
}

document.querySelectorAll('a[href="#adding"]').forEach(link => {
    link.addEventListener("click", (event) => {
        event.preventDefault(); 
        const section = document.getElementById("adding");
        
        section.scrollIntoView({ behavior: "smooth" });
        
        setTimeout(() => focusOnInput(), 500); 
    });
});

document.addEventListener('DOMContentLoaded', () => {
    // Check if the URL has the "scroll=true" query parameter
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('scroll') === 'true') {
        // Scroll to the bottom of the page
        window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });

        // Remove the query parameter from the URL without reloading the page
        const urlWithoutScroll = window.location.href.split('?')[0];
        window.history.replaceState({}, document.title, urlWithoutScroll);
    }
});
