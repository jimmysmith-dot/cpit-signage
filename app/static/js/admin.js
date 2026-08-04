"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const mediaTableBody = document.getElementById("media-table-body");
    const reorderStatus = document.getElementById("reorder-status");
    const mediaCount = document.getElementById("media-count");
    const pageLoadedTime = document.getElementById("page-loaded-time");
    const toastRegion = document.getElementById("toast-region");

    const uploadZone = document.getElementById("upload-zone");
    const fileInput = document.getElementById("media-files");
    const uploadStatus = document.getElementById("upload-status");

    const createSignForm = document.getElementById("create-sign-form");
    const createSignButton = document.getElementById("create-sign-button");
    const resetSignButton = document.getElementById("reset-sign-button");
    const createSignStatus = document.getElementById("create-sign-status");

    const templatePanel = document.getElementById("template-panel");
    const templateSelect = document.getElementById("sign-template");
    const templateDescription = document.getElementById(
        "template-description"
    );
    const applyTemplateButton = document.getElementById(
        "apply-template-button"
    );

    const logoUploadButton = document.getElementById(
        "logo-upload-button"
    );
    const logoFileInput = document.getElementById(
        "logo-file-input"
    );
    const logoGallery = document.getElementById("logo-gallery");
    const logoSelectionStatus = document.getElementById(
        "logo-selection-status"
    );
    const logoPosition = document.getElementById(
        "sign-logo-position"
    );
    const logoSize = document.getElementById("sign-logo-size");
    const logoSizeValue = document.getElementById(
        "sign-logo-size-value"
    );
    const logoMargin = document.getElementById(
        "sign-logo-margin"
    );
    const logoMarginValue = document.getElementById(
        "sign-logo-margin-value"
    );

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
    const previewLogo = document.getElementById("preview-logo");
    const previewAccent = document.getElementById("preview-accent");
    const previewContent = document.getElementById("preview-content");
    const previewTitle = document.getElementById("preview-title");
    const previewDivider = document.getElementById("preview-divider");
    const previewBody = document.getElementById("preview-body");
    const previewFooter = document.getElementById("preview-footer");

    let signTemplates = [];
    let logoLibrary = [];
    let selectedLogoFilename = "";

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
        overlayOpacity: 35,
        logoFilename: "",
        logoPosition: "top-right",
        logoWidthPercent: 18,
        logoMargin: 70
    };

    if (pageLoadedTime) {
        pageLoadedTime.textContent = new Intl.DateTimeFormat(undefined, {
            hour: "numeric",
            minute: "2-digit"
        }).format(new Date());
    }

    function showToast(message, isError = false, timeout = 4200) {
        if (!toastRegion || !message) {
            return;
        }

        const toast = document.createElement("div");
        toast.className = `toast${isError ? " error" : ""}`;

        const icon = document.createElement("span");
        icon.className = "toast-icon";
        icon.textContent = isError ? "!" : "✓";

        const messageElement = document.createElement("span");
        messageElement.className = "toast-message";
        messageElement.textContent = message;

        const closeButton = document.createElement("button");
        closeButton.type = "button";
        closeButton.className = "toast-close";
        closeButton.setAttribute("aria-label", "Dismiss notification");
        closeButton.textContent = "×";
        closeButton.addEventListener("click", () => toast.remove());

        toast.appendChild(icon);
        toast.appendChild(messageElement);
        toast.appendChild(closeButton);
        toastRegion.appendChild(toast);

        window.setTimeout(() => {
            toast.remove();
        }, timeout);
    }

    function setStatus(element, message, isError = false) {
        if (!element) {
            return;
        }
        element.textContent = message;
        element.classList.toggle("error", isError);
    }

    function setTemplateDescription(message, isError = false) {
        if (!templateDescription) {
            return;
        }

        templateDescription.textContent = message;
        templateDescription.style.color = isError
            ? "var(--danger)"
            : "";
    }

    function populateTemplateSelect(templates) {
        if (!templateSelect) {
            return;
        }

        templateSelect.innerHTML = "";

        templates.forEach((template) => {
            const option = document.createElement("option");
            option.value = template.id;
            option.textContent = template.name;
            templateSelect.appendChild(option);
        });

        templateSelect.disabled = templates.length === 0;

        if (applyTemplateButton) {
            applyTemplateButton.disabled = templates.length === 0;
        }

        if (templatePanel) {
            templatePanel.classList.remove("template-loading");
        }

        updateTemplateDescription();
    }

    function getSelectedTemplate() {
        if (!templateSelect) {
            return null;
        }

        return signTemplates.find(
            (template) => template.id === templateSelect.value
        ) || null;
    }

    function updateTemplateDescription() {
        const template = getSelectedTemplate();

        if (!template) {
            setTemplateDescription(
                "Choose a template to prefill the sign designer."
            );
            return;
        }

        setTemplateDescription(template.description);
    }

    function setColorControls(
        colorInput,
        hexInput,
        value
    ) {
        if (!colorInput || !hexInput) {
            return;
        }

        const normalized = normalizedHex(value, "#FFFFFF");
        colorInput.value = normalized.toLowerCase();
        hexInput.value = normalized;
    }

    function applyTemplate(template) {
        if (!template) {
            setStatus(
                createSignStatus,
                "Select a template before applying it.",
                true
            );
            return;
        }

        signTitle.value = template.title || "";
        signBody.value = template.body || "";
        signFooter.value = template.footer || "";
        signAlignment.value = template.alignment || "center";
        signDuration.value = String(template.duration || 10);

        setColorControls(
            backgroundColor,
            backgroundHex,
            template.background_color || DEFAULT_SIGN.backgroundColor
        );

        setColorControls(
            textColor,
            textHex,
            template.text_color || DEFAULT_SIGN.textColor
        );

        setColorControls(
            accentColor,
            accentHex,
            template.accent_color || DEFAULT_SIGN.accentColor
        );

        if (overlayOpacity) {
            overlayOpacity.value = String(
                template.overlay_opacity ?? DEFAULT_SIGN.overlayOpacity
            );
        }

        /*
         * Applying a template resets to a solid background. The user
         * may switch to a library image afterward without losing the
         * template's text, colors, alignment, or duration.
         */
        if (backgroundModeColor) {
            backgroundModeColor.checked = true;
        }

        if (backgroundModeImage) {
            backgroundModeImage.checked = false;
        }

        if (backgroundMedia) {
            backgroundMedia.value = "";
        }

        updateBackgroundControls();

        const message = `"${template.name}" template applied.`;
        setStatus(createSignStatus, message);
        showToast(message);
    }

    async function loadSignTemplates() {
        if (!templateSelect) {
            return;
        }

        try {
            const response = await fetch("/api/sign-templates");

            let result;

            try {
                result = await response.json();
            } catch (error) {
                throw new Error(
                    "The server returned an invalid template response."
                );
            }

            if (!response.ok) {
                throw new Error(
                    result.error || "Unable to load sign templates."
                );
            }

            if (!Array.isArray(result) || result.length === 0) {
                throw new Error(
                    "No sign templates are currently available."
                );
            }

            signTemplates = result;
            populateTemplateSelect(signTemplates);

        } catch (error) {
            console.error(error);

            if (templatePanel) {
                templatePanel.classList.remove("template-loading");
            }

            if (templateSelect) {
                templateSelect.innerHTML =
                    '<option value="">Templates unavailable</option>';
                templateSelect.disabled = true;
            }

            if (applyTemplateButton) {
                applyTemplateButton.disabled = true;
            }

            setTemplateDescription(error.message, true);
        }
    }

    function setLogoStatus(message, isError = false) {
        if (!logoSelectionStatus) {
            return;
        }

        logoSelectionStatus.textContent = message;
        logoSelectionStatus.style.color = isError
            ? "var(--danger)"
            : "";
    }

    function getSelectedLogo() {
        return logoLibrary.find(
            (logo) => logo.filename === selectedLogoFilename
        ) || null;
    }

    function selectLogo(filename) {
        selectedLogoFilename = filename || "";

        if (logoGallery) {
            logoGallery.querySelectorAll(".logo-card").forEach(
                (card) => {
                    card.classList.toggle(
                        "selected",
                        card.dataset.filename === selectedLogoFilename
                    );
                }
            );
        }

        const logo = getSelectedLogo();

        setLogoStatus(
            logo
                ? `Selected logo: ${logo.filename}`
                : "No logo selected."
        );

        updateSignPreview();
    }

    function renderLogoGallery() {
        if (!logoGallery) {
            return;
        }

        logoGallery.innerHTML = "";

        const noLogoCard = document.createElement("button");
        noLogoCard.type = "button";
        noLogoCard.className = "logo-card";
        noLogoCard.dataset.filename = "";
        noLogoCard.innerHTML = `
            <span class="logo-card-image-wrap">
                <span style="font-weight:850;color:#637381;">
                    No Logo
                </span>
            </span>
            <span class="logo-card-name">No branding</span>
        `;
        noLogoCard.addEventListener(
            "click",
            () => selectLogo("")
        );
        logoGallery.appendChild(noLogoCard);

        logoLibrary.forEach((logo) => {
            const card = document.createElement("div");
            card.className = "logo-card";
            card.dataset.filename = logo.filename;
            card.tabIndex = 0;
            card.setAttribute("role", "button");
            card.setAttribute(
                "aria-label",
                `Select logo ${logo.filename}`
            );

            const imageWrap = document.createElement("div");
            imageWrap.className = "logo-card-image-wrap";

            const image = document.createElement("img");
            image.src = logo.url;
            image.alt = "";
            image.loading = "lazy";
            imageWrap.appendChild(image);

            const name = document.createElement("span");
            name.className = "logo-card-name";
            name.textContent = logo.filename;

            const deleteButton = document.createElement("button");
            deleteButton.type = "button";
            deleteButton.className = "logo-delete-button";
            deleteButton.textContent = "×";
            deleteButton.title = `Delete ${logo.filename}`;
            deleteButton.setAttribute(
                "aria-label",
                `Delete logo ${logo.filename}`
            );

            deleteButton.addEventListener(
                "click",
                async (event) => {
                    event.stopPropagation();
                    await deleteLogo(logo);
                }
            );

            card.addEventListener(
                "click",
                () => selectLogo(logo.filename)
            );

            card.addEventListener(
                "keydown",
                (event) => {
                    if (
                        event.key === "Enter" ||
                        event.key === " "
                    ) {
                        event.preventDefault();
                        selectLogo(logo.filename);
                    }
                }
            );

            card.appendChild(imageWrap);
            card.appendChild(name);
            card.appendChild(deleteButton);
            logoGallery.appendChild(card);
        });

        selectLogo(selectedLogoFilename);
    }

    async function loadLogoLibrary() {
        if (!logoGallery) {
            return;
        }

        try {
            const response = await fetch("/api/logos");
            const result = await response.json();

            if (!response.ok) {
                throw new Error(
                    result.error || "Unable to load logo library."
                );
            }

            if (!Array.isArray(result)) {
                throw new Error(
                    "The server returned an invalid logo list."
                );
            }

            logoLibrary = result;

            if (
                selectedLogoFilename &&
                !logoLibrary.some(
                    (logo) =>
                        logo.filename === selectedLogoFilename
                )
            ) {
                selectedLogoFilename = "";
            }

            renderLogoGallery();

        } catch (error) {
            console.error(error);
            logoGallery.innerHTML = `
                <div class="logo-gallery-empty">
                    ${error.message}
                </div>
            `;
            setLogoStatus(error.message, true);
        }
    }

    async function uploadLogo(file) {
        if (!file) {
            return;
        }

        const formData = new FormData();
        formData.append("file", file);

        setLogoStatus(`Uploading ${file.name}...`);

        if (logoUploadButton) {
            logoUploadButton.disabled = true;
            logoUploadButton.textContent = "Uploading...";
        }

        try {
            const response = await fetch("/api/logos", {
                method: "POST",
                body: formData
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(
                    result.error || "The logo could not be uploaded."
                );
            }

            selectedLogoFilename = result.filename;
            await loadLogoLibrary();
            const message =
                `Logo uploaded and selected: ${result.filename}`;
            setLogoStatus(message);
            showToast(message);

        } catch (error) {
            console.error(error);
            setLogoStatus(error.message, true);

        } finally {
            if (logoFileInput) {
                logoFileInput.value = "";
            }

            if (logoUploadButton) {
                logoUploadButton.disabled = false;
                logoUploadButton.textContent = "Upload Logo";
            }
        }
    }

    async function deleteLogo(logo) {
        if (
            !window.confirm(
                `Delete logo "${logo.filename}"?\n\n` +
                "Generated signs that already contain this logo " +
                "will not be affected."
            )
        ) {
            return;
        }

        try {
            const response = await fetch(
                `/api/logos/${encodeURIComponent(logo.filename)}`,
                { method: "DELETE" }
            );

            const result = await response.json();

            if (!response.ok) {
                throw new Error(
                    result.error || "The logo could not be deleted."
                );
            }

            if (selectedLogoFilename === logo.filename) {
                selectedLogoFilename = "";
            }

            await loadLogoLibrary();
            const message = `Deleted logo: ${logo.filename}`;
            setLogoStatus(message);
            showToast(message);

        } catch (error) {
            console.error(error);
            setLogoStatus(error.message, true);
        }
    }

    function updateLogoControlLabels() {
        if (logoSizeValue && logoSize) {
            logoSizeValue.textContent = `${logoSize.value}%`;
        }

        if (logoMarginValue && logoMargin) {
            logoMarginValue.textContent = `${logoMargin.value}px`;
        }
    }

    function positionPreviewLogo(values) {
        if (!previewLogo) {
            return;
        }

        previewLogo.style.left = "";
        previewLogo.style.right = "";
        previewLogo.style.top = "";
        previewLogo.style.bottom = "";
        previewLogo.style.transform = "";

        const horizontalMargin =
            (values.logoMargin / 1920) * 100;
        const verticalMargin =
            (values.logoMargin / 1080) * 100;

        previewLogo.style.width =
            `${values.logoWidthPercent}%`;

        if (values.logoPosition.endsWith("left")) {
            previewLogo.style.left = `${horizontalMargin}%`;
        } else if (values.logoPosition.endsWith("right")) {
            previewLogo.style.right = `${horizontalMargin}%`;
        } else {
            previewLogo.style.left = "50%";
            previewLogo.style.transform = "translateX(-50%)";
        }

        if (values.logoPosition.startsWith("bottom")) {
            previewLogo.style.bottom = `${verticalMargin}%`;
        } else {
            previewLogo.style.top = `${verticalMargin}%`;
        }
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
                    : DEFAULT_SIGN.overlayOpacity,
            logoFilename: selectedLogoFilename,
            logoUrl: getSelectedLogo()
                ? getSelectedLogo().url
                : "",
            logoPosition: logoPosition
                ? logoPosition.value
                : DEFAULT_SIGN.logoPosition,
            logoWidthPercent: logoSize
                ? Number.parseInt(logoSize.value, 10)
                : DEFAULT_SIGN.logoWidthPercent,
            logoMargin: logoMargin
                ? Number.parseInt(logoMargin.value, 10)
                : DEFAULT_SIGN.logoMargin
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
        if (previewLogo) {
            if (values.logoFilename && values.logoUrl) {
                previewLogo.src = values.logoUrl;
                previewLogo.style.display = "block";
                positionPreviewLogo(values);
            } else {
                previewLogo.removeAttribute("src");
                previewLogo.style.display = "none";
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
        const hasContent =
            signTitle.value.trim() ||
            signBody.value.trim() ||
            signFooter.value.trim() ||
            selectedLogoFilename ||
            (backgroundModeImage && backgroundModeImage.checked);

        if (
            hasContent &&
            !window.confirm(
                "Clear the current designer settings?"
            )
        ) {
            return;
        }

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

        selectedLogoFilename = "";

        if (logoPosition) {
            logoPosition.value = DEFAULT_SIGN.logoPosition;
        }

        if (logoSize) {
            logoSize.value = String(
                DEFAULT_SIGN.logoWidthPercent
            );
        }

        if (logoMargin) {
            logoMargin.value = String(
                DEFAULT_SIGN.logoMargin
            );
        }

        updateLogoControlLabels();
        renderLogoGallery();
        updateBackgroundControls();
        setStatus(createSignStatus, "");
        updateSignPreview();
        showToast("Designer cleared.");
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

        if (
            !Number.isInteger(values.logoWidthPercent) ||
            values.logoWidthPercent < 5 ||
            values.logoWidthPercent > 40
        ) {
            throw new Error(
                "Logo size must be between 5 and 40 percent."
            );
        }

        if (
            !Number.isInteger(values.logoMargin) ||
            values.logoMargin < 0 ||
            values.logoMargin > 300
        ) {
            throw new Error(
                "Logo margin must be between 0 and 300 pixels."
            );
        }

        setStatus(createSignStatus, "Generating sign...");
        createSignButton.disabled = true;
        createSignButton.textContent = "Publishing...";

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
                overlay_opacity: values.overlayOpacity,
                logo_filename: values.logoFilename,
                logo_position: values.logoPosition,
                logo_width_percent: values.logoWidthPercent,
                logo_margin: values.logoMargin
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

        const message =
            "Sign published successfully and added to the playlist.";
        setStatus(createSignStatus, message);
        showToast(message, false, 5000);
        window.setTimeout(() => window.location.reload(), 1200);
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

        if (templateSelect) {
            templateSelect.addEventListener(
                "change",
                updateTemplateDescription
            );
        }

        if (applyTemplateButton) {
            applyTemplateButton.addEventListener(
                "click",
                () => {
                    applyTemplate(getSelectedTemplate());
                }
            );
        }

        if (logoUploadButton && logoFileInput) {
            logoUploadButton.addEventListener(
                "click",
                () => logoFileInput.click()
            );

            logoFileInput.addEventListener(
                "change",
                () => {
                    const [file] = logoFileInput.files;
                    uploadLogo(file);
                }
            );
        }

        [logoPosition, logoSize, logoMargin].forEach(
            (element) => {
                if (!element) {
                    return;
                }

                element.addEventListener(
                    "input",
                    () => {
                        updateLogoControlLabels();
                        updateSignPreview();
                    }
                );

                element.addEventListener(
                    "change",
                    () => {
                        updateLogoControlLabels();
                        updateSignPreview();
                    }
                );
            }
        );

        createSignForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            try {
                await createSign();
            } catch (error) {
                console.error(error);
                setStatus(createSignStatus, error.message, true);
                showToast(error.message, true);
                createSignButton.disabled = false;
                createSignButton.textContent = "Publish Sign";
            }
        });
    }

    if (resetSignButton) {
        resetSignButton.addEventListener("click", resetSignDesigner);
    }

    loadSignTemplates();
    loadLogoLibrary();
    updateLogoControlLabels();
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
            const message =
                `${files.length} file(s) uploaded successfully.`;
            setStatus(uploadStatus, message);
            showToast(message);
            window.setTimeout(() => window.location.reload(), 900);
        } catch (error) {
            console.error(error);
            setStatus(uploadStatus, error.message, true);
            showToast(error.message, true);
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
        showToast("Playlist order saved.");
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
                showToast(error.message, true);
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
                    const message =
                        `"${filename}" was deleted successfully.`;
                    setReorderStatus(message);
                    showToast(message);
                } else {
                    const message =
                        `"${filename}" was deleted. The playlist is now empty.`;
                    setReorderStatus(message);
                    showToast(message);
                }
            } catch (error) {
                console.error(error);
                setReorderStatus(error.message, true);
                showToast(error.message, true);
                button.disabled = false;
                button.textContent = "Delete";
            }
        });
    }

    refreshMediaCount();
    console.log("CPIT Signage Studio controls initialized.");
});
