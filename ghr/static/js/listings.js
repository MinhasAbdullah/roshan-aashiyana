  // Auto-submit on sort change
  document.getElementById('sortSelect').addEventListener('change', function() {
    document.getElementById('searchForm').submit();
  });

  // Pill radio — highlight on click
  document.querySelectorAll('.radio-pills .pill input').forEach(input => {
    input.addEventListener('change', () => {
      input.closest('.radio-pills').querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
      input.closest('.pill').classList.add('active');
    });
  });
    // suggestions Box
const searchInput = document.getElementById("searchInput");
const suggestionsBox = document.getElementById("suggestions");

searchInput.addEventListener("keyup", async function(){

    const query = this.value.trim();

    if(query.length < 2){
        suggestionsBox.innerHTML = "";
        suggestionsBox.style.display = "none";
        return;
    }

    const response = await fetch(`/autocomplete/?q=${query}`);
    const data = await response.json();

    suggestionsBox.innerHTML = "";

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

            // Auto submit search
            document.getElementById("searchForm").submit();
        };

        suggestionsBox.appendChild(div);
    });

    suggestionsBox.style.display =
        data.length > 0 ? "block" : "none";
});

document.addEventListener("click", function(e){

    if(
        !searchInput.contains(e.target) &&
        !suggestionsBox.contains(e.target)
    ){
        suggestionsBox.style.display = "none";
    }

});