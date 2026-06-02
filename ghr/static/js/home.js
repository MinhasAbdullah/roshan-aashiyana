  // CTA post btn opens modal
  const ctaPostBtn = document.getElementById('ctaPostBtn');
  if (ctaPostBtn) {
    ctaPostBtn.addEventListener('click', () => {
      document.getElementById('modal').classList.add('active');
      document.getElementById('authBox').classList.remove('signup-mode');
    });
  }

  // suggestions Box
const searchInput = document.getElementById("searchInput");
const suggestionsBox = document.getElementById("suggestions");

searchInput.addEventListener("keyup", async function() {

    const query = this.value.trim();

    if(query.length < 2){
        suggestionsBox.style.display = "none";
        suggestionsBox.innerHTML = "";
        return;
    }

    const response = await fetch(`/autocomplete/?q=${encodeURIComponent(query)}`);
    const data = await response.json();

    suggestionsBox.innerHTML = "";

    if(data.length === 0){
        suggestionsBox.style.display = "none";
        return;
    }

    data.forEach(item => {

    const div = document.createElement("div");

    div.className = "suggestion-item";

    div.innerHTML = `
        <i class="fa-solid fa-location-dot"></i>
        <span>${item}</span>
    `;

    div.onclick = () => {
        searchInput.value = item;
        suggestionsBox.style.display = "none";
    };

    suggestionsBox.appendChild(div);
    });

    suggestionsBox.style.display = "block";
});

document.addEventListener("click", function(e){

    if(!searchInput.contains(e.target) &&
       !suggestionsBox.contains(e.target)){

        suggestionsBox.style.display = "none";
    }
});