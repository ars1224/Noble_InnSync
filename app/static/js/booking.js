const adultsInput = document.querySelector('[name="adults"]');
const childrenInput = document.querySelector('[name="children"]');
const checkInInput = document.querySelector('[name="check_in"]');
const checkOutInput = document.querySelector('[name="check_out"]');

const suggestedRoomsList = document.getElementById("suggested-rooms-list");
const manualRoomsList = document.getElementById("manual-rooms-list");
const manualRoomMessage = document.getElementById("manual-room-message");

const selectedRoomIdsInput = document.getElementById("selected-room-ids");
const submitButton = document.querySelector(".booking-btn");

const roomModal = document.getElementById("room-modal");
const modifyRoomBtn = document.getElementById("modify-room-btn");
const closeModalBtn = document.getElementById("close-modal-btn");
const saveRoomBtn = document.getElementById("save-room-btn");
const roomModalOverlay = document.getElementById("room-modal-overlay");

const paymentSummaryMethod =
    document.getElementById("payment-summary-method");

let requiredCapacity = 1;
let manualRooms = [];
let selectedRooms = {};

function getStayNights() {
    if (!checkInInput.value || !checkOutInput.value) return 0;

    const checkIn = Date.parse(`${checkInInput.value}T00:00:00Z`);
    const checkOut = Date.parse(`${checkOutInput.value}T00:00:00Z`);
    const nights = Math.round((checkOut - checkIn) / 86400000);

    return nights > 0 ? nights : 0;
}

function getGuestValues() {
    return {
        adults: parseInt(adultsInput.value) || 1,
        children: parseInt(childrenInput.value) || 0
    };
}

async function updateSuggestedRooms() {

    const { adults, children } = getGuestValues();

    const params = new URLSearchParams({
        adults,
        children,
        check_in: checkInInput.value,
        check_out: checkOutInput.value
    });

    const response = await fetch(`/suggest-rooms?${params.toString()}`);

    const data = await response.json();

    requiredCapacity = data.required_capacity;

    if (!data.can_fit) {

        suggestedRoomsList.innerHTML = `
            <p class="suggestion-error">
                Not enough available room capacity.
            </p>
        `;

        return;
    }

    let html = "";

    data.selected_rooms.forEach(room => {

        html += `
            <div class="suggested-room-item">
                <span>${room.room_number} - ${room.room_type}</span>
                <strong>$${room.price.toFixed(2)} / night</strong>
            </div>
        `;
    });

    const stayText = data.nights
        ? `${data.nights} night(s)`
        : "Select valid dates";

    html += `
        <div class="suggested-room-total">
            <span>Rooms per night</span>
            <strong>$${data.nightly_total.toFixed(2)}</strong>
        </div>
        <div class="suggested-room-total">
            <span>Length of stay</span>
            <strong>${stayText}</strong>
        </div>
        <div class="suggested-room-total">
            <span>Total stay price</span>
            <strong>${data.nights ? `$${data.total_price.toFixed(2)}` : "Pending dates"}</strong>
        </div>
        <p class="suggested-capacity">
            Fits ${adults} adult(s) and ${children} child(ren)
        </p>
    `;

    suggestedRoomsList.innerHTML = html;

    // AUTO PRESELECT SUGGESTED ROOMS
    selectedRooms = {};

    data.selected_rooms.forEach(room => {

        if (!selectedRooms[room.room_type]) {
            selectedRooms[room.room_type] = 0;
        }

        selectedRooms[room.room_type] += 1;
    });

    renderManualRooms();

    submitButton.disabled = false;
}

async function loadManualRooms() {
    const response = await fetch("/available-room-options");
    const data = await response.json();

    manualRooms = data.rooms;
    selectedRooms = {};

    manualRooms.forEach(room => {
        selectedRooms[room.room_id] = 0;
    });

    renderManualRooms();
}

function renderManualRooms() {

    let groupedRooms = {};

    manualRooms.forEach(room => {

        if (!groupedRooms[room.room_type]) {

            groupedRooms[room.room_type] = {
                room_type: room.room_type,
                capacity: room.capacity,
                price: room.price,
                available_count: 0,
                room_ids: []
            };
        }

        groupedRooms[room.room_type].available_count += 1;
        groupedRooms[room.room_type].room_ids.push(room.room_id);
    });

    let html = "";

    Object.values(groupedRooms).forEach(group => {

        const quantity =
            selectedRooms[group.room_type] || 0;

        html += `
            <div class="manual-room-option">

                <div class="manual-room-info">

                    <strong>
                        ${group.room_type}
                    </strong>

                    <small>
                        ${group.available_count} room(s) available
                        · Capacity ${group.capacity} pax
                        · $${group.price.toFixed(2)}
                    </small>

                </div>

                <div class="quantity-control">

                    <button
                        type="button"
                        class="qty-btn"
                        onclick="changeRoomQuantity('${group.room_type}', -1)"
                    >
                        −
                    </button>

                    <span>${quantity}</span>

                    <button
                        type="button"
                        class="qty-btn"
                        onclick="changeRoomQuantity('${group.room_type}', 1)"
                    >
                        +
                    </button>

                </div>

            </div>
        `;
    });

    manualRoomsList.innerHTML = html;

    validateManualRooms();
}

function changeRoomQuantity(roomType, change) {

    const currentQuantity = selectedRooms[roomType] || 0;
    const newQuantity = currentQuantity + change;

    if (newQuantity < 0) {
        return;
    }

    const matchingRooms = manualRooms.filter(
        room => room.room_type === roomType
    );

    if (newQuantity > matchingRooms.length) {
        return;
    }

    let currentSelectedCapacity = 0;

    Object.entries(selectedRooms).forEach(([type, quantity]) => {
        const room = manualRooms.find(r => r.room_type === type);

        if (room) {
            currentSelectedCapacity += room.capacity * quantity;
        }
    });

    const selectedRoom = manualRooms.find(
        room => room.room_type === roomType
    );

    const nextCapacity =
        currentSelectedCapacity + (change * selectedRoom.capacity);

    if (change > 0 && currentSelectedCapacity >= requiredCapacity) {
        return;
    }

    selectedRooms[roomType] = newQuantity;
    renderManualRooms();
}

function validateManualRooms() {

    let selectedCapacity = 0;
    let selectedNightlyTotal = 0;
    let selectedIds = [];

    Object.entries(selectedRooms).forEach(([roomType, quantity]) => {

        if (quantity <= 0) {
            return;
        }

        const matchingRooms =
            manualRooms.filter(
                room => room.room_type === roomType
            );

        for (let i = 0; i < quantity; i++) {

            const room = matchingRooms[i];

            if (!room) {
                continue;
            }

            selectedCapacity += room.capacity;
            selectedNightlyTotal += room.price;

            selectedIds.push(room.room_id);
        }
    });

    selectedRoomIdsInput.value =
        selectedIds.join(",");

    if (selectedIds.length === 0) {

        manualRoomMessage.textContent =
            "Using recommended rooms.";

        manualRoomMessage.className =
            "manual-neutral";

        submitButton.disabled = false;

        return;
    }

    if (selectedCapacity >= requiredCapacity) {
        const nights = getStayNights();
        const stayTotal = selectedNightlyTotal * nights;

        manualRoomMessage.textContent =
            nights
                ? `Selected rooms fit all guests. $${selectedNightlyTotal.toFixed(2)} per night × ${nights} night(s) = $${stayTotal.toFixed(2)}.`
                : "Selected rooms fit all guests. Select valid dates to calculate the stay total.";

        manualRoomMessage.className =
            "manual-success";

        submitButton.disabled = false;

    } else {

        manualRoomMessage.textContent =
            "Please add more rooms to fit all guests.";

        manualRoomMessage.className =
            "manual-error";

        submitButton.disabled = true;
    }
}

function updateCustomerChoiceSummary() {
    let html = "";
    let nightlyTotal = 0;
    let hasManualSelection = false;
    const nights = getStayNights();

    Object.entries(selectedRooms).forEach(([roomType, quantity]) => {
        if (quantity <= 0) {
            return;
        }

        const room = manualRooms.find(r => r.room_type === roomType);

        if (!room) {
            return;
        }

        hasManualSelection = true;

        const lineTotal = room.price * quantity;
        nightlyTotal += lineTotal;

        html += `
            <div class="suggested-room-item">
                <span>${quantity} × ${roomType}</span>
                <strong>$${lineTotal.toFixed(2)} / night</strong>
            </div>
        `;
    });

    if (!hasManualSelection) {
        updateSuggestedRooms();
        return;
    }

    html += `
        <div class="suggested-room-total">
            <span>Rooms per night</span>
            <strong>$${nightlyTotal.toFixed(2)}</strong>
        </div>
        <div class="suggested-room-total">
            <span>Length of stay</span>
            <strong>${nights ? `${nights} night(s)` : "Select valid dates"}</strong>
        </div>
        <div class="suggested-room-total">
            <span>Total stay price</span>
            <strong>${nights ? `$${(nightlyTotal * nights).toFixed(2)}` : "Pending dates"}</strong>
        </div>

        <p class="suggested-capacity">
            Custom room selection saved.
        </p>
    `;

    suggestedRoomsList.innerHTML = html;
}

adultsInput.addEventListener("input", () => {
    selectedRoomIdsInput.value = "";
    updateSuggestedRooms();
    validateManualRooms();
});

childrenInput.addEventListener("input", () => {
    selectedRoomIdsInput.value = "";
    updateSuggestedRooms();
    validateManualRooms();
});

checkInInput.addEventListener("change", () => {
    updateSuggestedRooms();
    validateManualRooms();
});

checkOutInput.addEventListener("change", () => {
    updateSuggestedRooms();
    validateManualRooms();
});

modifyRoomBtn.addEventListener("click", () => {
    roomModal.classList.remove("hidden");
});

closeModalBtn.addEventListener("click", () => {
    roomModal.classList.add("hidden");
});

saveRoomBtn.addEventListener("click", () => {
    updateCustomerChoiceSummary();
    roomModal.classList.add("hidden");
});

roomModalOverlay.addEventListener("click", () => {
    roomModal.classList.add("hidden");
});

const paymentRadios =
    document.querySelectorAll('[name="payment_method"]');

const cardPaymentFields =
    document.getElementById("card-payment-fields");

paymentRadios.forEach(radio => {

    radio.addEventListener("change", () => {

        // UPDATE SUMMARY
        if (radio.checked && paymentSummaryMethod) {

            paymentSummaryMethod.textContent =
                radio.value;
        }

        // SHOW CARD FIELDS
        if (
            radio.value === "Card Payment"
            && radio.checked
        ) {

            cardPaymentFields.classList.remove("hidden");
        }

        // HIDE CARD FIELDS
        else if (
            radio.value === "Pay on Arrival"
            && radio.checked
        ) {

            cardPaymentFields.classList.add("hidden");
        }

    });

});

const bookingForm = document.querySelector(".booking-form");

bookingForm.addEventListener("submit", (event) => {
    const adults = parseInt(adultsInput.value) || 0;
    const children = parseInt(childrenInput.value) || 0;
    const checkIn = document.querySelector('[name="check_in"]').value;
    const checkOut = document.querySelector('[name="check_out"]').value;

    if (adults < 1) {
        alert("Please enter at least 1 adult.");
        event.preventDefault();
        return;
    }

    if (children < 0) {
        alert("Children cannot be negative.");
        event.preventDefault();
        return;
    }

    if (!checkIn || !checkOut) {
        alert("Please select both check-in and check-out dates.");
        event.preventDefault();
        return;
    }

    if (new Date(checkOut) <= new Date(checkIn)) {
        alert("Check-out date must be after check-in date.");
        event.preventDefault();
        return;
    }

    if (submitButton.disabled) {
        alert("Please select enough rooms to fit all guests.");
        event.preventDefault();
        return;
    }
});

const cardNumberInput =
    document.getElementById("card-number");

if (cardNumberInput) {

    cardNumberInput.addEventListener("input", () => {

        let value =
            cardNumberInput.value.replace(/\D/g, "");

        value = value.substring(0, 16);

        value = value.replace(
            /(\d{4})(?=\d)/g,
            "$1 "
        );

        cardNumberInput.value = value;
    });

}

const phoneNumberInput =
    document.getElementById("phone-number");

if (phoneNumberInput) {

    phoneNumberInput.addEventListener("input", () => {

        let value =
            phoneNumberInput.value.replace(/\D/g, "");

        value = value.substring(0, 10);

        if (value.length > 3 && value.length <= 6) {

            value =
                value.slice(0, 3) +
                " " +
                value.slice(3);

        }

        else if (value.length > 6) {

            value =
                value.slice(0, 3) +
                " " +
                value.slice(3, 6) +
                " " +
                value.slice(6);

        }

        phoneNumberInput.value = value;
    });

}

const expiryDateInput =
    document.getElementById("expiry-date");

if (expiryDateInput) {

    expiryDateInput.addEventListener("input", () => {

        let value =
            expiryDateInput.value.replace(/\D/g, "");

        value = value.substring(0, 4);

        if (value.length >= 3) {

            value =
                value.slice(0, 2) +
                "/" +
                value.slice(2);
        }

        expiryDateInput.value = value;
    });

}

const cvvInput =
    document.getElementById("cvv");

if (cvvInput) {

    cvvInput.addEventListener("input", () => {

        cvvInput.value =
            cvvInput.value
                .replace(/\D/g, "")
                .slice(0, 3);
    });

}


updateSuggestedRooms();
loadManualRooms();
