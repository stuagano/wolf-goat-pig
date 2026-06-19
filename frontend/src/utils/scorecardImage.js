// Client-side scorecard image preprocessing. Normalizes rotation from
// EXIF, downscales oversized phone-camera shots, and re-encodes to JPEG
// so the vision model receives a clean, predictable input. Falls back
// to the original file if anything in the pipeline can't run (e.g. the
// browser doesn't support createImageBitmap with imageOrientation, or
// the file is HEIC and we can't decode it client-side).

// Keep phone-camera resolution: scorecards are dense handwritten grids and that
// detail is what makes the cells legible to the vision model. We only cap at a
// generous ceiling (huge panoramas) and re-orient via EXIF; the BACKEND then
// sizes the image to the highest resolution that fits Groq's request budget.
const MAX_DIMENSION = 4096;
const JPEG_QUALITY = 0.9;

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
