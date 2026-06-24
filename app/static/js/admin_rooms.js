document.addEventListener("DOMContentLoaded", () => {
    const modal = document.querySelector("[data-maintenance-modal]");
    const modalForm = modal?.querySelector("[data-maintenance-form]");
    const roomOption = modal?.querySelector("[data-maintenance-room-option]");
    const subtitle = modal?.querySelector("[data-maintenance-subtitle]");
    const equipmentInput = modal?.querySelector("[data-maintenance-equipment]");
    const closeButtons = modal?.querySelectorAll("[data-maintenance-close]") || [];
    let activeStatusForm = null;

    const closeModal = () => {
        if (!modal) {
            return;
        }

        modal.hidden = true;
        document.body.classList.remove("modal-open");
        activeStatusForm = null;
    };

    const openModal = (statusForm) => {
        activeStatusForm = statusForm;
        modalForm.action = statusForm.action;
        roomOption.textContent = `Room ${statusForm.dataset.roomNumber}`;
        subtitle.textContent = `Room ${statusForm.dataset.roomNumber} will be taken out of service.`;
        modalForm.reset();
        modal.hidden = false;
        document.body.classList.add("modal-open");
        equipmentInput.focus();
    };

    document.querySelectorAll("[data-room-status-form]").forEach((statusForm) => {
        const statusSelect = statusForm.querySelector("[data-room-status-select]");
        const submitButton = statusForm.querySelector("[data-room-status-submit]");

        const updateButtonLabel = () => {
            submitButton.textContent = statusSelect.value === "Maintenance"
                ? "Set Room to Maintenance"
                : "Update";
        };

        statusSelect.addEventListener("change", updateButtonLabel);
        updateButtonLabel();

        statusForm.addEventListener("submit", (event) => {
            const isMaintenanceStatus = statusSelect.value === "Maintenance";

            if (isMaintenanceStatus && modal) {
                event.preventDefault();
                openModal(statusForm);
            }
        });
    });

    modalForm?.addEventListener("submit", () => {
        if (activeStatusForm) {
            modalForm.action = activeStatusForm.action;
        }
    });

    closeButtons.forEach((button) => button.addEventListener("click", closeModal));

    modal?.addEventListener("click", (event) => {
        if (event.target === modal) {
            closeModal();
        }
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && modal && !modal.hidden) {
            closeModal();
        }
    });
});
