"use strict";

const player = document.getElementById("player");
const statusMessage = document.getElementById("status");

let slides = [];
let currentIndex = 0;
let activeElement = null;
let nextElement = null;
let timer = null;

async function loadPlaylist() {
    try {
        const response = await fetch("/api/slides", {
            cache: "no-store"
        });

        if (!response.ok) {
            throw new Error(`Playlist request failed: ${response.status}`);
        }

        slides = await response.json();

        if (!Array.isArray(slides) || slides.length === 0) {
            statusMessage.textContent = "No signage content is available.";
            return;
        }

        statusMessage.remove();
        preloadAndStart();
    } catch (error) {
        console.error(error);
        statusMessage.textContent = "Unable to load signage content.";

        setTimeout(loadPlaylist, 10000);
    }
}

function createImageElement(slide) {
    const image = document.createElement("img");

    image.className = "slide";
    image.src = slide.url;
    image.alt = "";
    image.draggable = false;

    return image;
}

function preloadAndStart() {
    activeElement = createImageElement(slides[0]);
    player.appendChild(activeElement);

    activeElement.addEventListener(
        "load",
        () => {
            activeElement.classList.add("active");
            scheduleNextSlide();
        },
        { once: true }
    );

    activeElement.addEventListener(
        "error",
        () => {
            console.error(`Unable to load ${slides[0].url}`);
            advanceSlide();
        },
        { once: true }
    );
}

function scheduleNextSlide() {
    clearTimeout(timer);

    const durationSeconds = Number(slides[currentIndex].duration) || 10;

    timer = setTimeout(advanceSlide, durationSeconds * 1000);
}

function advanceSlide() {
    const nextIndex = (currentIndex + 1) % slides.length;
    const nextSlide = slides[nextIndex];

    nextElement = createImageElement(nextSlide);
    player.appendChild(nextElement);

    nextElement.addEventListener(
        "load",
        () => {
            requestAnimationFrame(() => {
                nextElement.classList.add("active");
                activeElement.classList.remove("active");
            });

            setTimeout(() => {
                activeElement.remove();
                activeElement = nextElement;
                nextElement = null;
                currentIndex = nextIndex;

                scheduleNextSlide();
            }, 1000);
        },
        { once: true }
    );

    nextElement.addEventListener(
        "error",
        () => {
            console.error(`Unable to load ${nextSlide.url}`);
            nextElement.remove();
            currentIndex = nextIndex;
            scheduleNextSlide();
        },
        { once: true }
    );
}

loadPlaylist();
