"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const mediaTableBody = document.getElementById("media-table-body");
    const reorderStatus = document.getElementById("reorder-status");
    const mediaCount = document.getElementById("media-count");
    const pageLoadedTime = document.getElementById("page-loaded-time");

    const uploadZone = document.getElementById("upload-zone");
    const fileInput = document.getElementById("media-files");
    const uploadStatus = document.getElementById("upload-status");

    const createSignForm = document.getElementById("create-sign-form");
    const createSignButton = document.getElementById("create-sign-button");
    const resetSignButton = document.getElementById("reset-sign-button");
    const createSignStatus = document.getElementById("create-sign-status");

    const signTitle = document.getElementById("sign-title");
    const signBody = document.getElementById("sign-body");
    const signFooter = document.getElementById("sign-footer");
    const signAlignment = document.getElementById("sign-alignment");
    const signDuration = document.getElementById("sign-duration");

    const backgroundColor = document.getElementById("sign-background-color");
    const backgroundHex = document.getElementById("sign-background-hex");
    const textColor = document.getElementById("sign-text-color");
    const textHex = document.getElementById("sign-text-hex");
    const accentColor = document.getElementById("sign-accent-color");
    const accentHex = document.getElementById("sign-accent-hex");

    const backgroundModeColor = document.getElementById(
        "background-mode-color"
    );
    const backgroundModeImage = document.getElementById(
        "background-mode-image"
    );
    const solidBackgroundOptions = document.getElementById(
        "solid-background-options"
    );
    const imageBackgroundOptions = document.getElementById(
        "image-background-options"
    );
    const overlayOptions = document.getElementById("overlay-options");
    const backgroundMedia = document.getElementById(
        "sign-background-media"
    );
    const overlayOpacity = document.getElementById(
        "sign-overlay-opacity"
    );
    const overlayValue = document.getElementById(
        "sign-overlay-value"
    );

    const signPreview = document.getElementById("sign-preview");
    const previewBackgroundImage = document.getElementById(
        "preview-background-image"
    );
    const previewOverlay = document.getElementById("preview-overlay");
    const previewAccent = document.getElementById("preview-accent");
    const previewContent = document.getElementById("preview-content");
    const previewTitle = document.getElementById("preview-title");
    const previewDivider = document.getElementById("preview-divider");
    const previewBody = document.getElementById("preview-body");
    const previewFooter = document.getElementById("preview-footer");

    const DEFAULT_SIGN = {
        title: "Lobby Remodel Update",
        body: "Our lobby renovation begins soon.\nThank you for your patience.",
        footer: "We appreciate you staying with us.",
        backgroundColor: "#153A5B",
        textColor: "#FFFFFF",
        accentColor: "#75B9E6",
        alignment: "center",
        duration: 10,
        backgroundMode: "color",
        backgroundMediaId: null,
        overlayOpacity: 35
    };

    if (pageLoadedTime) {
        pageLoadedTime.textContent = new Intl.DateTimeFormat(undefined, {
            hour: "numeric",
            minute: "2-digit"
        }).format(new Date());
    }

    function setStatus(element, message, isError = false) {
        if (!element) {
            return;
        }
        element.textContent = message;
        element.classList.toggle("error", isError);
    }

    function refreshMediaCount() {
        if (!mediaCount) {
            return;
        }
        const count = mediaTableBody
            ? mediaTableBody.querySelectorAll(".media-row").length
            : 0;
        mediaCount.textContent = String(count);
    }

    function validHex(value) {
        return /^#[0-9A-F]{6}$/i.test(value.trim());
    }

    function normalizedHex(value, fallback) {
        const candidate = value.trim();
        const withHash = candidate.startsWith("#")
            ? candidate
            : `#${candidate}`;
        return validHex(withHash) ? withHash.toUpperCase() : fallback;
    }

    function syncColorPair(colorInput, hexInput, fallback) {
        if (!colorInput || !hexInput) {
            return;
        }

        colorInput.addEventListener("input", () => {
            hexInput.value = colorInput.value.toUpperCase();
            updateSignPreview();
        });

        hexInput.addEventListener("input", () => {
            const value = normalizedHex(hexInput.value, fallback);
            if (validHex(value)) {
                colorInput.value = value;
            }
            updateSignPreview();
        });

        hexInput.addEventListener("blur", () => {
            const value = normalizedHex(hexInput.value, fallback);
            hexInput.value = value;
            colorInput.value = value;
            updateSignPreview();
        });
    }

    function getSignValues() {
        return {
            title: signTitle ? signTitle.value.trim() : "",
            body: signBody ? signBody.value.trim() : "",
            footer: signFooter ? signFooter.value.trim() : "",
            alignment: signAlignment ? signAlignment.value : "center",
            duration: signDuration
                ? Number.parseInt(signDuration.value, 10)
                : 10,
            backgroundColor: normalizedHex(
                backgroundHex ? backgroundHex.value : "",
                DEFAULT_SIGN.backgroundColor
            ),
            textColor: normalizedHex(
                textHex ? textHex.value : "",
                DEFAULT_SIGN.textColor
            ),
            accentColor: normalizedHex(
                accentHex ? accentHex.value : "",
                DEFAULT_SIGN.accentColor
            ),
            backgroundMode:
                backgroundModeImage && backgroundModeImage.checked
                    ? "image"
                    : "color",
            backgroundMediaId:
                backgroundMedia && backgroundMedia.value
                    ? Number.parseInt(backgroundMedia.value, 10)
                    : null,
            backgroundImageUrl:
                backgroundMedia &&
                backgroundMedia.selectedOptions.length
                    ? backgroundMedia.selectedOptions[0].dataset.url || ""
                    : "",
            overlayOpacity:
                overlayOpacity
                    ? Number.parseInt(overlayOpacity.value, 10)
                    : DEFAULT_SIGN.overlayOpacity
        };
    }

    function updateBackgroundControls() {
        const useImage =
            backgroundModeImage && backgroundModeImage.checked;

        if (solidBackgroundOptions) {
            solidBackgroundOptions.hidden = useImage;
        }

        if (imageBackgroundOptions) {
            imageBackgroundOptions.hidden = !useImage;
        }

        if (overlayOptions) {
            overlayOptions.hidden = !useImage;
        }

        if (overlayValue && overlayOpacity) {
            overlayValue.textContent = `${overlayOpacity.value}%`;
        }

        updateSignPreview();
    }

    function updateSignPreview() {
        if (!signPreview) {
            return;
        }

        const values = getSignValues();

        const useImage =
            values.backgroundMode === "image" &&
            Boolean(values.backgroundImageUrl);

        signPreview.style.backgroundColor = values.backgroundColor;
        signPreview.style.color = values.textColor;

        if (previewBackgroundImage && previewOverlay) {
            previewBackgroundImage.style.display = useImage
                ? "block"
                : "none";

            previewOverlay.style.display = useImage
                ? "block"
                : "none";

            if (useImage) {
                previewBackgroundImage.src =
                    values.backgroundImageUrl;

                previewOverlay.style.background =
                    `rgba(0, 0, 0, ${values.overlayOpacity / 100})`;
            } else {
                previewBackgroundImage.removeAttribute("src");
            }
        }
        previewAccent.style.backgroundColor = values.accentColor;
        previewDivider.style.backgroundColor = values.accentColor;
        previewContent.style.textAlign = values.alignment;
        previewFooter.style.textAlign = values.alignment;

        previewTitle.textContent = values.title || "Your title will appear here";
        previewBody.textContent = values.body || "Your message will appear here.";
        previewFooter.textContent = values.footer;
        previewFooter.hidden = !values.footer;
        previewDivider.classList.toggle("hidden", !values.title || !values.body);
    }

    function resetSignDesigner() {
        signTitle.value = "";
        signBody.value = "";
        signFooter.value = "";
        signAlignment.value = DEFAULT_SIGN.alignment;
        signDuration.value = String(DEFAULT_SIGN.duration);

        backgroundColor.value = DEFAULT_SIGN.backgroundColor.toLowerCase();
        backgroundHex.value = DEFAULT_SIGN.backgroundColor;
        textColor.value = DEFAULT_SIGN.textColor.toLowerCase();
        textHex.value = DEFAULT_SIGN.textColor;
        accentColor.value = DEFAULT_SIGN.accentColor.toLowerCase();
        accentHex.value = DEFAULT_SIGN.accentColor;

        if (backgroundModeColor) {
            backgroundModeColor.checked = true;
        }

        if (backgroundModeImage) {
            backgroundModeImage.checked = false;
        }

        if (backgroundMedia) {
            backgroundMedia.value = "";
        }

        if (overlayOpacity) {
            overlayOpacity.value = String(
                DEFAULT_SIGN.overlayOpacity
            );
        }

        updateBackgroundControls();
        setStatus(createSignStatus, "");
        updateSignPreview();
    }

    async function createSign() {
        const values = getSignValues();

        if (!values.title && !values.body) {
            throw new Error("Enter a title or message before creating the sign.");
        }

        if (!Number.isInteger(values.duration) || values.duration < 1 || values.duration > 3600) {
            throw new Error("Duration must be between 1 and 3600 seconds.");
        }

        if (
            values.backgroundMode === "image" &&
            !Number.isInteger(values.backgroundMediaId)
        ) {
            throw new Error(
                "Select a background image from the media library."
            );
        }

        if (
            !Number.isInteger(values.overlayOpacity) ||
            values.overlayOpacity < 0 ||
            values.overlayOpacity > 100
        ) {
            throw new Error(
                "Overlay opacity must be between 0 and 100."
            );
        }

        setStatus(createSignStatus, "Generating sign...");
        createSignButton.disabled = true;
        createSignButton.textContent = "Creating...";

        const response = await fetch("/api/slides/create", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                title: values.title,
                body: values.body,
                footer: values.footer,
                background_color: values.backgroundColor,
                text_color: values.textColor,
                accent_color: values.accentColor,
                alignment: values.alignment,
                duration: values.duration,
                background_media_id:
                    values.backgroundMode === "image"
                        ? values.backgroundMediaId
                        : null,
                overlay_opacity: values.overlayOpacity
            })
        });

        let result;
        try {
            result = await response.json();
        } catch (error) {
            throw new Error("The server returned an invalid slide response.");
        }

        if (!response.ok) {
            throw new Error(result.error || "The sign could not be created.");
        }

        setStatus(createSignStatus, "Sign created successfully. Refreshing...");
        window.setTimeout(() => window.location.reload(), 900);
    }

    if (createSignForm) {
        [signTitle, signBody, signFooter, signAlignment, signDuration].forEach((element) => {
            element.addEventListener("input", updateSignPreview);
            element.addEventListener("change", updateSignPreview);
        });

        syncColorPair(backgroundColor, backgroundHex, DEFAULT_SIGN.backgroundColor);
        syncColorPair(textColor, textHex, DEFAULT_SIGN.textColor);
        syncColorPair(accentColor, accentHex, DEFAULT_SIGN.accentColor);

        [
            backgroundModeColor,
            backgroundModeImage
        ].forEach((element) => {
            if (element) {
                element.addEventListener(
                    "change",
                    updateBackgroundControls
                );
            }
        });

        if (backgroundMedia) {
            backgroundMedia.addEventListener(
                "change",
                updateSignPreview
            );
        }

        if (overlayOpacity) {
            overlayOpacity.addEventListener(
                "input",
                updateBackgroundControls
            );
        }

        createSignForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            try {
                await createSign();
            } catch (error) {
                console.error(error);
                setStatus(createSignStatus, error.message, true);
                createSignButton.disabled = false;
                createSignButton.textContent = "Create Sign";
            }
        });
    }

    if (resetSignButton) {
        resetSignButton.addEventListener("click", resetSignDesigner);
    }

    updateBackgroundControls();

    function preventFileNavigation(event) {
        const types = event.dataTransfer
            ? Array.from(event.dataTransfer.types || [])
            : [];
        if (!types.includes("Files")) {
            return;
        }
        event.preventDefault();
        event.stopPropagation();
    }

    async function uploadFile(file, currentNumber, totalFiles) {
        const formData = new FormData();
        formData.append("file", file);
        setStatus(uploadStatus, `Uploading ${currentNumber} of ${totalFiles}: ${file.name}`);

        const response = await fetch("/api/media", {
            method: "POST",
            body: formData
        });

        let result;
        try {
            result = await response.json();
        } catch (error) {
            throw new Error(`The server returned an invalid response for ${file.name}.`);
        }

        if (!response.ok) {
            throw new Error(result.error || `Upload failed for ${file.name}.`);
        }
    }

    async function uploadFiles(fileList) {
        const files = Array.from(fileList);
        if (!files.length) {
            return;
        }

        fileInput.disabled = true;
        uploadZone.classList.add("uploading");

        try {
            for (let index = 0; index < files.length; index += 1) {
                await uploadFile(files[index], index + 1, files.length);
            }
            setStatus(uploadStatus, `${files.length} file(s) uploaded successfully.`);
            window.setTimeout(() => window.location.reload(), 800);
        } catch (error) {
            console.error(error);
            setStatus(uploadStatus, error.message, true);
        } finally {
            fileInput.disabled = false;
            uploadZone.classList.remove("uploading");
            fileInput.value = "";
        }
    }

    if (uploadZone && fileInput) {
        ["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
            document.addEventListener(eventName, preventFileNavigation, false);
        });

        ["dragenter", "dragover"].forEach((eventName) => {
            uploadZone.addEventListener(eventName, (event) => {
                preventFileNavigation(event);
                uploadZone.classList.add("drag-active");
            });
        });

        ["dragleave", "drop"].forEach((eventName) => {
            uploadZone.addEventListener(eventName, (event) => {
                preventFileNavigation(event);
                uploadZone.classList.remove("drag-active");
            });
        });

        uploadZone.addEventListener("drop", (event) => uploadFiles(event.dataTransfer.files));
        uploadZone.addEventListener("click", () => fileInput.click());
        uploadZone.addEventListener("keydown", (event) => {
            if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                fileInput.click();
            }
        });
        fileInput.addEventListener("change", () => uploadFiles(fileInput.files));
    }

    let draggedRow = null;

    function setReorderStatus(message, isError = false) {
        setStatus(reorderStatus, message, isError);
    }

    function updateVisibleOrderNumbers() {
        if (!mediaTableBody) {
            return;
        }
        Array.from(mediaTableBody.querySelectorAll(".media-row")).forEach((row, index) => {
            const input = row.querySelector('input[name^="order_"]');
            if (input) {
                input.value = index + 1;
            }
        });
    }

    function getOrderedMediaIds() {
        if (!mediaTableBody) {
            return [];
        }
        return Array.from(mediaTableBody.querySelectorAll(".media-row")).map((row) => {
            const mediaId = Number.parseInt(row.dataset.mediaId, 10);
            if (!Number.isInteger(mediaId)) {
                throw new Error(`Invalid media ID found in playlist row: ${row.dataset.mediaId}`);
            }
            return mediaId;
        });
    }

    async function saveRowOrder() {
        const mediaIds = getOrderedMediaIds();
        if (!mediaIds.length) {
            return;
        }

        setReorderStatus("Saving playlist order...");
        const response = await fetch("/api/media/reorder", {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ media_ids: mediaIds })
        });

        let result;
        try {
            result = await response.json();
        } catch (error) {
            throw new Error("The server returned an invalid reorder response.");
        }

        if (!response.ok) {
            throw new Error(result.error || "Unable to save playlist order.");
        }

        updateVisibleOrderNumbers();
        setReorderStatus("Playlist order saved.");
    }

    if (mediaTableBody) {
        mediaTableBody.addEventListener("dragstart", (event) => {
            const handle = event.target.closest(".drag-handle");
            if (!handle) {
                event.preventDefault();
                return;
            }
            const row = handle.closest(".media-row");
            if (!row || !row.dataset.mediaId) {
                event.preventDefault();
                setReorderStatus("Unable to identify the selected media row.", true);
                return;
            }
            draggedRow = row;
            row.classList.add("dragging");
            event.dataTransfer.effectAllowed = "move";
            event.dataTransfer.setData("text/plain", row.dataset.mediaId);
        });

        mediaTableBody.addEventListener("dragend", () => {
            if (draggedRow) {
                draggedRow.classList.remove("dragging");
            }
            mediaTableBody.querySelectorAll(".drag-over").forEach((row) => row.classList.remove("drag-over"));
            draggedRow = null;
        });

        mediaTableBody.addEventListener("dragover", (event) => {
            if (!draggedRow) {
                return;
            }
            event.preventDefault();
            const targetRow = event.target.closest(".media-row");
            if (!targetRow || targetRow === draggedRow) {
                return;
            }
            mediaTableBody.querySelectorAll(".drag-over").forEach((row) => row.classList.remove("drag-over"));
            targetRow.classList.add("drag-over");
            const rectangle = targetRow.getBoundingClientRect();
            const insertAfter = event.clientY > rectangle.top + rectangle.height / 2;
            if (insertAfter) {
                targetRow.after(draggedRow);
            } else {
                targetRow.before(draggedRow);
            }
        });

        mediaTableBody.addEventListener("drop", async (event) => {
            if (!draggedRow) {
                return;
            }
            event.preventDefault();
            mediaTableBody.querySelectorAll(".drag-over").forEach((row) => row.classList.remove("drag-over"));
            try {
                updateVisibleOrderNumbers();
                await saveRowOrder();
            } catch (error) {
                console.error(error);
                setReorderStatus(error.message, true);
            }
        });

        mediaTableBody.addEventListener("click", async (event) => {
            const button = event.target.closest(".delete-button");
            if (!button) {
                return;
            }

            const mediaId = Number.parseInt(button.dataset.mediaId, 10);
            const filename = button.dataset.filename || "this media item";
            if (!Number.isInteger(mediaId)) {
                setReorderStatus("Unable to identify the selected media item.", true);
                return;
            }

            if (!window.confirm(`Delete "${filename}"?\n\nThis permanently removes the database record and media file.`)) {
                return;
            }

            button.disabled = true;
            button.textContent = "Deleting...";

            try {
                const response = await fetch(`/api/media/${mediaId}`, { method: "DELETE" });
                const result = await response.json();
                if (!response.ok) {
                    throw new Error(result.error || "Unable to delete media.");
                }

                const row = button.closest(".media-row");
                if (row) {
                    row.remove();
                }
                refreshMediaCount();
                updateVisibleOrderNumbers();

                if (getOrderedMediaIds().length) {
                    await saveRowOrder();
                    setReorderStatus(`"${filename}" was deleted successfully.`);
                } else {
                    setReorderStatus(`"${filename}" was deleted. The playlist is now empty.`);
                }
            } catch (error) {
                console.error(error);
                setReorderStatus(error.message, true);
                button.disabled = false;
                button.textContent = "Delete";
            }
        });
    }

    refreshMediaCount();
    console.log("CPIT Signage admin and sign designer controls initialized.");
});
