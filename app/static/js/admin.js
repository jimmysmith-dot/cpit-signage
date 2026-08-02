"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const uploadZone = document.getElementById("upload-zone");
    const fileInput = document.getElementById("media-files");
    const uploadStatus = document.getElementById("upload-status");

    if (!uploadZone || !fileInput || !uploadStatus) {
        console.error("CPIT upload controls were not found.", {
            uploadZone,
            fileInput,
            uploadStatus
        });
        return;
    }

    function preventDefaults(event) {
        event.preventDefault();
        event.stopPropagation();
    }

    function setStatus(message, isError = false) {
        uploadStatus.textContent = message;
        uploadStatus.classList.toggle("error", isError);
    }

    async function uploadFile(file, currentNumber, totalFiles) {
        const formData = new FormData();
        formData.append("file", file);

        setStatus(
            `Uploading ${currentNumber} of ${totalFiles}: ${file.name}`
        );

        const response = await fetch("/api/media", {
            method: "POST",
            body: formData
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(
                result.error || `Upload failed for ${file.name}`
            );
        }

        return result;
    }

    async function uploadFiles(fileList) {
        const files = Array.from(fileList);

        if (files.length === 0) {
            return;
        }

        fileInput.disabled = true;
        uploadZone.classList.add("uploading");

        try {
            for (let index = 0; index < files.length; index += 1) {
                await uploadFile(
                    files[index],
                    index + 1,
                    files.length
                );
            }

            setStatus(
                `${files.length} file(s) uploaded successfully.`
            );

            window.setTimeout(() => {
                window.location.reload();
            }, 800);

        } catch (error) {
            console.error(error);
            setStatus(error.message, true);

        } finally {
            fileInput.disabled = false;
            uploadZone.classList.remove("uploading");
            fileInput.value = "";
        }
    }

    ["dragenter", "dragover", "dragleave", "drop"].forEach(
        (eventName) => {
            document.addEventListener(
                eventName,
                preventDefaults,
                false
            );
        }
    );

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

    console.log("CPIT Signage upload controls initialized.");
});
