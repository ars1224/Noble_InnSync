document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("[data-booking-edit]");

    if (!form) {
        return;
    }

    const checkInInput = form.querySelector("[data-edit-check-in]");
    const checkOutInput = form.querySelector("[data-edit-check-out]");
    const nightsOutput = form.querySelector("[data-edit-nights]");
    const totalOutput = form.querySelector("[data-edit-total]");
    const submitButton = form.querySelector("[data-edit-submit]");
    const nightlyTotal = Number(form.dataset.nightlyTotal || 0);
    const millisecondsPerDay = 24 * 60 * 60 * 1000;

    const parseDate = (value) => {
        if (!value) {
            return null;
        }

        const date = new Date(`${value}T00:00:00Z`);
        return Number.isNaN(date.getTime()) ? null : date;
    };

    const updatePricePreview = () => {
        const checkIn = parseDate(checkInInput.value);
        const checkOut = parseDate(checkOutInput.value);
        let nights = 0;

        if (checkIn && checkOut) {
            nights = Math.round((checkOut - checkIn) / millisecondsPerDay);
        }

        const hasValidStay = nights > 0;
        checkOutInput.setCustomValidity(
            checkIn && checkOut && !hasValidStay
                ? "Check-out must be after check-in."
                : ""
        );

        nightsOutput.textContent = hasValidStay ? String(nights) : "0";
        totalOutput.textContent = hasValidStay
            ? (nightlyTotal * nights * 1.15).toFixed(2)
            : "0.00";
    };

    checkInInput.addEventListener("change", updatePricePreview);
    checkOutInput.addEventListener("change", updatePricePreview);

    form.addEventListener("submit", () => {
        if (!form.checkValidity()) {
            return;
        }

        submitButton.disabled = true;
        submitButton.innerHTML = '<i class="fa-solid fa-spinner fa-spin" aria-hidden="true"></i> Saving...';
    });

    updatePricePreview();
});
