// Client-side scorecard image preprocessing. Normalizes rotation from
// EXIF, downscales oversized phone-camera shots, and re-encodes to JPEG
// so the vision model receives a clean, predictable input. Falls back
// to the original file if anything in the pipeline can't run (e.g. the
// browser doesn't support createImageBitmap with imageOrientation, or
// the file is HEIC and we can't decode it client-side).

// Keep as much scorecard detail as the backend can actually use. The backend
// caps its OpenCV preprocessing at 3000px on the longest side (its sweet spot:
// fast, and avoids the low-res over-crop that 2048 caused) — match that here so
// phone pics aren't pre-shrunk below what the backend works at, while still
// re-orienting via EXIF. Uploading larger just gets downscaled at the backend.
const MAX_DIMENSION = 3000;
const JPEG_QUALITY = 0.85;

export async function preprocessScorecardImage(file) {
  if (!file || !file.type?.startsWith("image/")) return file;
  if (typeof createImageBitmap !== "function") return file;

  let bitmap;
  try {
    bitmap = await createImageBitmap(file, { imageOrientation: "from-image" });
  } catch {
    // Some browsers reject the imageOrientation option; try without it.
    try {
      bitmap = await createImageBitmap(file);
    } catch {
      return file;
    }
  }

  let { width, height } = bitmap;
  const longest = Math.max(width, height);
  const needsResize = longest > MAX_DIMENSION;
  if (needsResize) {
    const scale = MAX_DIMENSION / longest;
    width = Math.round(width * scale);
    height = Math.round(height * scale);
  }

  // Skip the round-trip entirely if the source is already small AND a JPEG —
  // re-encoding tiny PNGs can hurt OCR quality and wastes CPU.
  if (!needsResize && file.type === "image/jpeg") {
    bitmap.close?.();
    return file;
  }

  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d");
  if (!ctx) {
    bitmap.close?.();
    return file;
  }
  ctx.drawImage(bitmap, 0, 0, width, height);
  bitmap.close?.();

  const blob = await new Promise((resolve) =>
    canvas.toBlob((b) => resolve(b), "image/jpeg", JPEG_QUALITY),
  );
  if (!blob) return file;

  const baseName = (file.name || "scorecard").replace(/\.\w+$/, "");
  return new File([blob], `${baseName}.jpg`, { type: "image/jpeg" });
}

export async function downscaleToBase64(file, maxDim = 1200) {
  if (!file || typeof createImageBitmap !== "function") return null;
  try {
    let bitmap;
    try {
      bitmap = await createImageBitmap(file, { imageOrientation: "from-image" });
    } catch {
      bitmap = await createImageBitmap(file);
    }
    let { width, height } = bitmap;
    const longest = Math.max(width, height);
    if (longest > maxDim) {
      const scale = maxDim / longest;
      width = Math.round(width * scale);
      height = Math.round(height * scale);
    }
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext("2d");
    if (!ctx) { bitmap.close?.(); return null; }
    ctx.drawImage(bitmap, 0, 0, width, height);
    bitmap.close?.();
    const dataUrl = canvas.toDataURL("image/jpeg", 0.7);
    return dataUrl && dataUrl.startsWith("data:image") ? dataUrl : null;
  } catch {
    return null;
  }
}
