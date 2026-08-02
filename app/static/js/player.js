"use strict";

const player = document.getElementById("player");

const POLL_INTERVAL_MS = 15000;
const TRANSITION_MS = 1000;

let slides = [];
let playlistSignature = "";
let currentIndex = 0;
let activeElement = null;
let slideTimer = null;
let pollTimer = null;
let transitionInProgress = false;

function slideKey(slide) {
    return String(slide.id ?? slide.url);
}

function createPlaylistSignature(playlist) {
    return JSON.stringify(
        playlist.map((slide) => ({
            id: slide.id,
            type: slide.type,
            url: slide.url,
            duration: slide.duration,
            sort_order: slide.sort_order
        }))
    );
}

function showStatus(message) {
    let status = document.getElementById("status");

    if (!status) {
        status = document.createElement("div");
        status.id = "status";
        player.appendChild(status);
    }

    status.textContent = message;
}

function removeStatus() {
    const status = document.getElementById("status");

    if (status) {
        status.remove();
    }
}

async function fetchPlaylist() {
    const response = await fetch("/api/slides", {
        cache: "no-store"
    });

    if (!response.ok) {
        throw new Error(
            `Playlist request failed with status ${response.status}`
        );
    }

    const result = await response.json();

    if (!Array.isArray(result)) {
        throw new Error("Playlist response was not an array");
    }

    return result;
}

function createSlideElement(slide) {
    if (slide.type !== "image") {
        throw new Error(`Unsupported media type: ${slide.type}`);
    }

    const image = document.createElement("img");

    image.className = "slide";
    image.src = slide.url;
    image.alt = "";
    image.draggable = false;
    image.dataset.slideKey = slideKey(slide);

    return image;
}

function scheduleNextSlide() {
    window.clearTimeout(slideTimer);

    if (slides.length === 0) {
        return;
    }

    const durationSeconds =
        Number(slides[currentIndex].duration) || 10;

    slideTimer = window.setTimeout(
        advanceSlide,
        durationSeconds * 1000
    );
}

function displayFirstSlide() {
    if (slides.length === 0) {
        showStatus("No signage content is available.");
        return;
    }

    removeStatus();

    currentIndex = 0;
    const element = createSlideElement(slides[currentIndex]);

    element.addEventListener(
        "load",
        () => {
            player.appendChild(element);

            requestAnimationFrame(() => {
                element.classList.add("active");
            });

            activeElement = element;
            scheduleNextSlide();
        },
        { once: true }
    );

    element.addEventListener(
        "error",
        () => {
            console.error(
                `Unable to load ${slides[currentIndex].url}`
            );

            currentIndex =
                (currentIndex + 1) % slides.length;

            displayFirstSlide();
        },
        { once: true }
    );
}

function transitionToIndex(nextIndex) {
    if (
        transitionInProgress ||
        slides.length === 0 ||
        !activeElement
    ) {
        return;
    }

    transitionInProgress = true;

    const nextSlide = slides[nextIndex];
    const nextElement = createSlideElement(nextSlide);

    nextElement.addEventListener(
        "load",
        () => {
            player.appendChild(nextElement);

            requestAnimationFrame(() => {
                nextElement.classList.add("active");
                activeElement.classList.remove("active");
            });

            window.setTimeout(() => {
                activeElement.remove();
                activeElement = nextElement;
                currentIndex = nextIndex;
                transitionInProgress = false;

                scheduleNextSlide();
            }, TRANSITION_MS);
        },
        { once: true }
    );

    nextElement.addEventListener(
        "error",
        () => {
            console.error(`Unable to load ${nextSlide.url}`);

            transitionInProgress = false;
            currentIndex = nextIndex;
            scheduleNextSlide();
        },
        { once: true }
    );
}

function advanceSlide() {
    if (slides.length === 0) {
        return;
    }

    const nextIndex = (currentIndex + 1) % slides.length;
    transitionToIndex(nextIndex);
}

function applyUpdatedPlaylist(updatedSlides) {
    const currentKey = activeElement
        ? activeElement.dataset.slideKey
        : null;

    slides = updatedSlides;

    if (slides.length === 0) {
        window.clearTimeout(slideTimer);

        if (activeElement) {
            activeElement.remove();
            activeElement = null;
        }

        currentIndex = 0;
        showStatus("No signage content is available.");
        return;
    }

    removeStatus();

    if (!activeElement) {
        displayFirstSlide();
        return;
    }

    const matchingIndex = slides.findIndex(
        (slide) => slideKey(slide) === currentKey
    );

    if (matchingIndex >= 0) {
        currentIndex = matchingIndex;

        // Apply any updated duration to the current slide.
        scheduleNextSlide();
        return;
    }

    // The currently displayed slide was removed or disabled.
    transitionToIndex(0);
}

async function checkForPlaylistUpdates() {
    try {
        const updatedSlides = await fetchPlaylist();
        const updatedSignature =
            createPlaylistSignature(updatedSlides);

        if (updatedSignature !== playlistSignature) {
            console.log("Playlist change detected.");

            playlistSignature = updatedSignature;
            applyUpdatedPlaylist(updatedSlides);
        }
    } catch (error) {
        console.error("Playlist polling failed:", error);
    }
}

async function initializePlayer() {
    try {
        slides = await fetchPlaylist();
        playlistSignature = createPlaylistSignature(slides);

        if (slides.length === 0) {
            showStatus("No signage content is available.");
        } else {
            displayFirstSlide();
        }
    } catch (error) {
        console.error(error);
        showStatus("Unable to load signage content.");
    }

    pollTimer = window.setInterval(
        checkForPlaylistUpdates,
        POLL_INTERVAL_MS
    );
}

initializePlayer();
