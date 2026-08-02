"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const mediaTableBody = document.querySelector("tbody");
    const reorderStatus = document.getElementById("reorder-status");

    const uploadZone = document.getElementById("upload-zone");
    const fileInput = document.getElementById("media-files");
    const uploadStatus = document.getElementById("upload-status");

    /*
     * Upload controls
     */

    function preventDefaults(event) {
        event.preventDefault();
        event.stopPropagation();
    }

    function setUploadStatus(message, isError = false) {
        if (!uploadStatus) {
            return;
        }

        uploadStatus.textContent = message;
        uploadStatus.classList.toggle("error", isError);
    }

    async function uploadFile(file, currentNumber, totalFiles) {
        const formData = new FormData();
        formData.append("file", file);

        setUploadStatus(
            `Uploading ${currentNumber} of ${totalFiles}: ${file.name}`
        );

        const response = await fetch("/api/media", {
            method: "POST",
            body: formData
        });

        let result;

        try {
            result = await response.json();
        } catch (error) {
            throw new Error(
                `The server returned an invalid response for ${file.name}.`
            );
        }

        if (!response.ok) {
            throw new Error(
                result.error || `Upload failed for ${file.name}.`
            );
        }

        return result;
    }

    async function uploadFiles(fileList) {
        const files = Array.from(fileList);

        if (files.length === 0) {
            return;
        }

        if (!fileInput || !uploadZone) {
            setUploadStatus(
                "The upload controls are unavailable.",
                true
            );
            return;
        }

        fileInput.disabled = true;
        uploadZone.classList.add("uploading");

        try {
            for (
                let index = 0;
                index < files.length;
                index += 1
            ) {
                await uploadFile(
                    files[index],
                    index + 1,
                    files.length
                );
            }

            setUploadStatus(
                `${files.length} file(s) uploaded successfully.`
            );

            window.setTimeout(() => {
                window.location.reload();
            }, 800);

        } catch (error) {
            console.error(error);
            setUploadStatus(error.message, true);

        } finally {
            fileInput.disabled = false;
            uploadZone.classList.remove("uploading");
            fileInput.value = "";
        }
    }

    if (uploadZone && fileInput && uploadStatus) {
        /*
         * Prevent the browser from opening a dropped file.
         */
        [
            "dragenter",
            "dragover",
            "dragleave",
            "drop"
        ].forEach((eventName) => {
            document.addEventListener(
                eventName,
                preventDefaults,
                false
            );
        });

        ["dragenter", "dragover"].forEach((eventName) => {
            uploadZone.addEventListener(eventName, () => {
                uploadZone.classList.add("drag-active");
            });
        });

        ["dragleave", "drop"].forEach((eventName) => {
            uploadZone.addEventListener(eventName, () => {
                uploadZone.classList.remove("drag-active");
            });
        });

        uploadZone.addEventListener("drop", (event) => {
            uploadFiles(event.dataTransfer.files);
        });

        uploadZone.addEventListener("click", () => {
            fileInput.click();
        });

        uploadZone.addEventListener("keydown", (event) => {
            if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                fileInput.click();
            }
        });

        fileInput.addEventListener("change", () => {
            uploadFiles(fileInput.files);
        });

    } else {
        console.error("CPIT upload controls were not found.", {
            uploadZone,
            fileInput,
            uploadStatus
        });
    }

    /*
     * Playlist ordering controls
     */

    let draggedRow = null;

    function setReorderStatus(message, isError = false) {
        if (!reorderStatus) {
            return;
        }

        reorderStatus.textContent = message;
        reorderStatus.classList.toggle("error", isError);
    }

    function updateVisibleOrderNumbers() {
        if (!mediaTableBody) {
            return;
        }

        const rows = Array.from(
            mediaTableBody.querySelectorAll(".media-row")
        );

        rows.forEach((row, index) => {
            const orderInput = row.querySelector(
                'input[name^="order_"]'
            );

            if (orderInput) {
                orderInput.value = index + 1;
            }
        });
    }

    function getOrderedMediaIds() {
        if (!mediaTableBody) {
            return [];
        }

        const rows = Array.from(
            mediaTableBody.querySelectorAll(".media-row")
        );

        return rows.map((row) => {
            const value = row.dataset.mediaId;
            const mediaId = Number.parseInt(value, 10);

            if (!Number.isInteger(mediaId)) {
                throw new Error(
                    `Invalid media ID found in playlist row: ${value}`
                );
            }

            return mediaId;
        });
    }

    async function saveRowOrder() {
        if (!mediaTableBody) {
            return;
        }

        const mediaIds = getOrderedMediaIds();

        if (mediaIds.length === 0) {
            return;
        }

        setReorderStatus("Saving playlist order...");

        const response = await fetch("/api/media/reorder", {
            method: "PUT",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                media_ids: mediaIds
            })
        });

        let result;

        try {
            result = await response.json();
        } catch (error) {
            throw new Error(
                "The server returned an invalid reorder response."
            );
        }

        if (!response.ok) {
            throw new Error(
                result.error || "Unable to save playlist order."
            );
        }

        updateVisibleOrderNumbers();
        setReorderStatus("Playlist order saved.");
    }

    if (mediaTableBody) {
        mediaTableBody.addEventListener(
            "dragstart",
            (event) => {
                const handle = event.target.closest(
                    ".drag-handle"
                );

                if (!handle) {
                    event.preventDefault();
                    return;
                }

                const row = handle.closest(".media-row");

                if (!row || !row.dataset.mediaId) {
                    event.preventDefault();

                    setReorderStatus(
                        "Unable to identify the selected media row.",
                        true
                    );

                    return;
                }

                draggedRow = row;
                row.classList.add("dragging");

                event.dataTransfer.effectAllowed = "move";

                event.dataTransfer.setData(
                    "text/plain",
                    row.dataset.mediaId
                );
            }
        );

        mediaTableBody.addEventListener("dragend", () => {
            if (draggedRow) {
                draggedRow.classList.remove("dragging");
            }

            mediaTableBody
                .querySelectorAll(".drag-over")
                .forEach((row) => {
                    row.classList.remove("drag-over");
                });

            draggedRow = null;
        });

        mediaTableBody.addEventListener(
            "dragover",
            (event) => {
                if (!draggedRow) {
                    return;
                }

                event.preventDefault();

                const targetRow = event.target.closest(
                    ".media-row"
                );

                if (
                    !targetRow ||
                    targetRow === draggedRow
                ) {
                    return;
                }

                mediaTableBody
                    .querySelectorAll(".drag-over")
                    .forEach((row) => {
                        row.classList.remove("drag-over");
                    });

                targetRow.classList.add("drag-over");

                const rectangle =
                    targetRow.getBoundingClientRect();

                const insertAfter =
                    event.clientY >
                    rectangle.top + rectangle.height / 2;

                if (insertAfter) {
                    targetRow.after(draggedRow);
                } else {
                    targetRow.before(draggedRow);
                }
            }
        );

        mediaTableBody.addEventListener(
            "drop",
            async (event) => {
                if (!draggedRow) {
                    return;
                }

                event.preventDefault();

                mediaTableBody
                    .querySelectorAll(".drag-over")
                    .forEach((row) => {
                        row.classList.remove("drag-over");
                    });

                try {
                    updateVisibleOrderNumbers();
                    await saveRowOrder();

                } catch (error) {
                    console.error(error);

                    setReorderStatus(
                        error.message,
                        true
                    );
                }
            }
        );
    }

    /*
     * Delete controls
     */

    async function deleteMedia(button) {
        const mediaId = Number.parseInt(
            button.dataset.mediaId,
            10
        );

        const filename =
            button.dataset.filename || "this media item";

        if (!Number.isInteger(mediaId)) {
            setReorderStatus(
                "Unable to identify the selected media item.",
                true
            );

            return;
        }

        const confirmed = window.confirm(
            `Delete "${filename}"?\n\n` +
            "This permanently removes both the database " +
            "record and the media file."
        );

        if (!confirmed) {
            return;
        }

        button.disabled = true;
        button.textContent = "Deleting...";

        try {
            const response = await fetch(
                `/api/media/${mediaId}`,
                {
                    method: "DELETE"
                }
            );

            let result;

            try {
                result = await response.json();
            } catch (error) {
                throw new Error(
                    "The server returned an invalid delete response."
                );
            }

            if (!response.ok) {
                throw new Error(
                    result.error || "Unable to delete media."
                );
            }

            const row = button.closest(".media-row");

            if (row) {
                row.remove();
            }

            updateVisibleOrderNumbers();

            /*
             * Save the new sequential order after removal.
             */
            const remainingIds = getOrderedMediaIds();

            if (remainingIds.length > 0) {
                await saveRowOrder();
            } else {
                setReorderStatus(
                    `"${filename}" was deleted. ` +
                    "The playlist is now empty."
                );
            }

            if (remainingIds.length > 0) {
                setReorderStatus(
                    `"${filename}" was deleted successfully.`
                );
            }

        } catch (error) {
            console.error(error);

            setReorderStatus(
                error.message,
                true
            );

            button.disabled = false;
            button.textContent = "Delete";
        }
    }

    if (mediaTableBody) {
        /*
         * Event delegation also supports buttons added after an upload
         * and page refresh.
         */
        mediaTableBody.addEventListener(
            "click",
            (event) => {
                const button = event.target.closest(
                    ".delete-button"
                );

                if (!button) {
                    return;
                }

                deleteMedia(button);
            }
        );
    }

    console.log(
        "CPIT Signage admin controls initialized."
    );
});
