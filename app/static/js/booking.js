const adultsInput = document.querySelector('[name="adults"]');
const childrenInput = document.querySelector('[name="children"]');
const suggestedRoomsList = document.getElementById("suggested-rooms-list");
const hiddenTotalPrice = document.getElementById("hidden-total-price");

async function updateSuggestedRooms() {
    const adults = parseInt(adultsInput.value) || 1;
    const children = parseInt(childrenInput.value) || 0;

    const response = await fetch(`/suggest-rooms?adults=${adults}&children=${children}`);
    const data = await response.json();

    if (!data.can_fit) {
        suggestedRoomsList.innerHTML = `
            <p class="suggestion-error">
                Not enough available room capacity.
            </p>
        `;
        hiddenTotalPrice.value = 0;
        return;
    }

    let html = "";

    data.selected_rooms.forEach(room => {
        html += `
            <div class="suggested-room-item">
                <span>${room.room_number} - ${room.room_type}</span>
                <strong>$${room.price}</strong>
            </div>
        `;
    });

    html += `
        <div class="suggested-room-total">
            <span>Total</span>
            <strong>$${data.total_price.toFixed(2)}</strong>
        </div>

        <p class="suggested-capacity">
            Capacity: ${data.total_adult_capacity} adult(s), ${data.total_child_capacity} child(ren)
        </p>
    `;

    suggestedRoomsList.innerHTML = html;
    hiddenTotalPrice.value = data.total_price;
}

adultsInput.addEventListener("input", updateSuggestedRooms);
childrenInput.addEventListener("input", updateSuggestedRooms);

updateSuggestedRooms();