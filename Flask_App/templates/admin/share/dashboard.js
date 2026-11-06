document.addEventListener("DOMContentLoaded", () => {

    console.log("La Beauté Admin Ready");

    // Active Sidebar Hover Effect
    const links = document.querySelectorAll(".sidebar-menu .nav-link");

    links.forEach(link => {

        link.addEventListener("mouseenter", () => {

            link.style.transform = "translateX(4px)";

        });

        link.addEventListener("mouseleave", () => {

            link.style.transform = "translateX(0px)";

        });

    });

});

