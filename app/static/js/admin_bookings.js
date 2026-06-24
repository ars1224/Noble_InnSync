const bookingToolbar = document.querySelector("[data-booking-toolbar]");
const bookingRows = document.querySelectorAll("[data-booking-row]");

if (bookingToolbar && bookingRows.length) {
    const referenceLabel = bookingToolbar.querySelector("[data-selected-reference]");
    const guestLabel = bookingToolbar.querySelector("[data-selected-guest]");
    const actionGroup = bookingToolbar.querySelector("[data-selection-actions]");
    const mutationForm = bookingToolbar.querySelector("[data-booking-mutation-form]");
    const toolbarActions = {
        view: bookingToolbar.querySelector('[data-booking-action="view"]'),
        edit: bookingToolbar.querySelector('[data-booking-action="edit"]'),
        payment: bookingToolbar.querySelector('[data-booking-action="payment"]'),
        confirm: bookingToolbar.querySelector('[data-booking-action="confirm"]'),
        cancel: bookingToolbar.querySelector('[data-booking-action="cancel"]'),
        checkin: bookingToolbar.querySelector('[data-booking-action="checkin"]'),
        checkout: bookingToolbar.querySelector('[data-booking-action="checkout"]'),
        delete: bookingToolbar.querySelector('[data-booking-action="delete"]'),
    };

    const setAction = (action, url) => {
        if (!action) return;
        action.hidden = !url;
        if (url) action.href = url;
    };

    const selectBooking = (row) => {
        bookingRows.forEach((bookingRow) => {
            const isSelected = bookingRow === row;
            bookingRow.classList.toggle("is-selected", isSelected);
            bookingRow.setAttribute("aria-selected", String(isSelected));
            bookingRow.querySelector(".booking-row-selector").checked = isSelected;
        });

        referenceLabel.textContent = row.dataset.reference;
        guestLabel.textContent = `${row.dataset.guest} · ${row.dataset.status}`;
        actionGroup.hidden = false;

        setAction(toolbarActions.view, row.dataset.viewUrl);
        setAction(toolbarActions.edit, row.dataset.editUrl);
        setAction(toolbarActions.payment, row.dataset.paymentUrl);
        setAction(toolbarActions.confirm, row.dataset.confirmUrl);
        setAction(toolbarActions.cancel, row.dataset.cancelUrl);
        setAction(toolbarActions.checkin, row.dataset.checkinUrl);
        setAction(toolbarActions.checkout, row.dataset.checkoutUrl);
        setAction(toolbarActions.delete, row.dataset.deleteUrl);
    };

    bookingRows.forEach((row) => {
        row.addEventListener("click", (event) => {
            if (event.target.closest("a, button")) return;
            selectBooking(row);
        });

        row.addEventListener("keydown", (event) => {
            if (event.target.closest("a, button, input")) return;
            if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                selectBooking(row);
            }
        });

        row.querySelector(".booking-row-selector").addEventListener("change", () => {
            selectBooking(row);
        });
    });

    ["confirm", "cancel", "checkin", "checkout", "delete"].forEach((name) => {
        const action = toolbarActions[name];
        if (!action || !mutationForm) return;

        action.addEventListener("click", (event) => {
            event.preventDefault();
            if (
                name === "delete"
                && !window.confirm(`Delete booking ${referenceLabel.textContent}? This cannot be undone.`)
            ) {
                return;
            }

            mutationForm.action = action.href;
            mutationForm.submit();
        });
    });
}
