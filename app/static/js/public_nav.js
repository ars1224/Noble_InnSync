const publicHeader = document.querySelector("[data-public-header]");
const hero = document.querySelector(".hero");
const mobileNav = document.querySelector("[data-mobile-nav]");

if (publicHeader) {
    const updateHeader = () => {
        const overHero = hero && window.scrollY < Math.max(hero.offsetHeight - 96, 0);
        publicHeader.classList.toggle("is-over-hero", Boolean(overHero));
        publicHeader.classList.toggle("is-solid", !overHero);
    };

    updateHeader();
    window.addEventListener("scroll", updateHeader, { passive: true });
    window.addEventListener("resize", updateHeader);

    publicHeader.querySelectorAll("a").forEach((link) => {
        link.addEventListener("click", () => mobileNav?.removeAttribute("open"));
    });

    document.addEventListener("click", (event) => {
        if (mobileNav?.open && !mobileNav.contains(event.target)) {
            mobileNav.removeAttribute("open");
        }
    });
}
