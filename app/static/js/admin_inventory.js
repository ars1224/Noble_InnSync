document.addEventListener("DOMContentLoaded", () => {
    const modal = document.querySelector("[data-inventory-modal]");

    if (!modal) {
        return;
    }

    const title = modal.querySelector("[data-inventory-title]");
    const subtitle = modal.querySelector("[data-inventory-subtitle]");
    const statusBadge = modal.querySelector("[data-inventory-status]");
    const updateForm = modal.querySelector("[data-inventory-update-form]");
    const addForm = modal.querySelector("[data-inventory-add-form]");
    const alertForm = modal.querySelector("[data-inventory-alert-form]");
    const nameInput = modal.querySelector("[data-inventory-name-input]");
    const categoryInput = modal.querySelector("[data-inventory-category-input]");
    const stockInput = modal.querySelector("[data-inventory-stock-input]");
    const reorderInput = modal.querySelector("[data-inventory-reorder-input]");
    const unitInput = modal.querySelector("[data-inventory-unit-input]");
    const closeButtons = modal.querySelectorAll("[data-inventory-close]");

    const ensureCategoryOption = (category) => {
        const exists = Array.from(categoryInput.options).some((option) => (
            option.value === category
        ));

        if (!exists && category) {
            categoryInput.add(new Option(category, category));
        }
    };

    const openModal = (button) => {
        const data = button.dataset;

        title.textContent = data.itemName;
        subtitle.textContent = `${data.category} - ${data.currentStock} ${data.unit} on hand`;
        statusBadge.textContent = data.status;
        statusBadge.className = `record-status status-${data.statusKey}`;

        updateForm.action = data.updateUrl;
        addForm.action = data.addUrl;
        alertForm.action = data.alertUrl;

        nameInput.value = data.itemName;
        ensureCategoryOption(data.category);
        categoryInput.value = data.category;
        stockInput.value = data.currentStock;
        reorderInput.value = data.reorderLevel;
        unitInput.value = data.unit;

        alertForm.hidden = data.alertNeeded !== "true";
        modal.hidden = false;
        document.body.classList.add("modal-open");
        nameInput.focus();
    };

    const closeModal = () => {
        modal.hidden = true;
        document.body.classList.remove("modal-open");
    };

    document.querySelectorAll("[data-inventory-open]").forEach((button) => {
        button.addEventListener("click", () => openModal(button));
    });

    closeButtons.forEach((button) => {
        button.addEventListener("click", closeModal);
    });

    modal.addEventListener("click", (event) => {
        if (event.target === modal) {
            closeModal();
        }
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && !modal.hidden) {
            closeModal();
        }
    });
});
