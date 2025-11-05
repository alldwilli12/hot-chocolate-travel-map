// Initialize Leaflet map
var map = L.map("map").setView([48.8566, 2.3522], 4);

// Add OpenStreetMap tile layer
L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
}).addTo(map);

// Get toggle elements if they exist (only shown for logged-in users)
const toggle = document.getElementById("mySpotsToggle");
const toggleLabel = document.getElementById("toggleLabel");

// Store all spots and marker references globally
let allSpots = [];
let markers = [];

// Helper Function: render spots on the map
function renderSpots(spots) {
    // Remove all existing markers
    markers.forEach((m) => map.removeLayer(m));
    markers = [];

    // Add new markers
    spots.forEach((spot) => {
        if (spot.lat && spot.lon) {
            const marker = L.marker([spot.lat, spot.lon]).addTo(map);
            let popupContent = `
        <div class="popup-content" style="text-align:center;">
          <h3 class="popup-title">${spot.name}</h3>
          <p class="popup-address">${spot.address}</p>
          <p class="popup-rating"> ${"⭐".repeat(Math.round(spot.rating))} (${spot.rating}/5)</p>
      `;

            if (spot.image_path) {
                popupContent += `
        <img src="/static/${spot.image_path}" alt="Hot chocolate spot photo" class="popup-img">
      `;
            }

            popupContent += `
          <p class="popup-notes mt-2"><em>${spot.notes || ""}</em></p>
        </div>
      `;

            marker.bindPopup(popupContent);
            markers.push(marker);
        }
    });
}

// Helper Function: fetch and render all spots
function loadAllSpots() {
    fetch("/spots")
        .then((response) => response.json())
        .then((spots) => {
            allSpots = spots;
            renderSpots(allSpots);
        })
        .catch((error) => console.error("Error fetching all spots:", error));
}

// Helper Function: fetch and render only the user's spots
function loadMySpots() {
    fetch("/my_spots")
        .then((response) => response.json())
        .then((spots) => renderSpots(spots))
        .catch((error) => console.error("Error fetching my spots:", error));
}

// Initialize map markers when the page loads
loadAllSpots();

// Set up toggle listener (only runs if user is logged in)
if (toggle) {
    toggle.addEventListener("change", () => {
        if (toggle.checked) {
            toggleLabel.textContent = "Showing only my spots ☕";
            loadMySpots();
        } else {
            toggleLabel.textContent = "Show only my spots";
            renderSpots(allSpots);
        }
    });
}
