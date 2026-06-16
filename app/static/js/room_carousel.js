document.querySelectorAll("[data-room-carousel]").forEach((carousel) => {
    const slides = Array.from(carousel.querySelectorAll("[data-carousel-slide]"));
    const indicators = Array.from(
        carousel.querySelectorAll("[data-carousel-indicator]")
    );
    const previousButton = carousel.querySelector("[data-carousel-previous]");
    const nextButton = carousel.querySelector("[data-carousel-next]");
    const currentLabel = carousel.querySelector("[data-carousel-current]");

    if (!slides.length) return;

    let activeIndex = 0;
    let touchStartX = null;

    const showSlide = (index) => {
        activeIndex = (index + slides.length) % slides.length;

        slides.forEach((slide, slideIndex) => {
            const isActive = slideIndex === activeIndex;
            slide.classList.toggle("is-active", isActive);
            slide.setAttribute("aria-hidden", String(!isActive));
        });

        indicators.forEach((indicator, indicatorIndex) => {
            const isActive = indicatorIndex === activeIndex;
            indicator.classList.toggle("is-active", isActive);
            indicator.setAttribute("aria-current", String(isActive));
        });

        if (currentLabel) currentLabel.textContent = String(activeIndex + 1);
    };

    previousButton?.addEventListener("click", () => showSlide(activeIndex - 1));
    nextButton?.addEventListener("click", () => showSlide(activeIndex + 1));

    indicators.forEach((indicator) => {
        indicator.addEventListener("click", () => {
            showSlide(Number(indicator.dataset.carouselIndicator));
        });
    });

    carousel.addEventListener("keydown", (event) => {
        if (event.key === "ArrowLeft") showSlide(activeIndex - 1);
        if (event.key === "ArrowRight") showSlide(activeIndex + 1);
    });

    carousel.addEventListener(
        "touchstart",
        (event) => {
            touchStartX = event.changedTouches[0].clientX;
        },
        { passive: true }
    );

    carousel.addEventListener(
        "touchend",
        (event) => {
            if (touchStartX === null) return;
            const distance = event.changedTouches[0].clientX - touchStartX;

            if (Math.abs(distance) > 50) {
                showSlide(activeIndex + (distance < 0 ? 1 : -1));
            }

            touchStartX = null;
        },
        { passive: true }
    );
});
