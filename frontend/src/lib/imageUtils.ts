/**
 * Compress an image to reduce file size
 * @param base64 - The base64 string of the image
 * @param maxWidth - Maximum width in pixels (default 1200)
 * @param quality - JPEG quality 0-1 (default 0.7)
 * @returns Compressed base64 string
 */
export async function compressImage(
  base64: string,
  maxWidth: number = 1200,
  quality: number = 0.7
): Promise<string> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      // Calculate new dimensions
      let width = img.width;
      let height = img.height;

      if (width > maxWidth) {
        height = (height * maxWidth) / width;
        width = maxWidth;
      }

      // Create canvas and draw resized image
      const canvas = document.createElement('canvas');
      canvas.width = width;
      canvas.height = height;

      const ctx = canvas.getContext('2d');
      if (!ctx) {
        reject(new Error('Could not get canvas context'));
        return;
      }

      ctx.drawImage(img, 0, 0, width, height);

      // Export as JPEG with compression
      const compressed = canvas.toDataURL('image/jpeg', quality);
      resolve(compressed);
    };

    img.onerror = () => {
      // If compression fails, return original
      resolve(base64);
    };

    img.src = base64;
  });
}

/**
 * Get approximate size of base64 string in KB
 */
export function getBase64SizeKB(base64: string): number {
  // Remove data URL prefix if present
  const base64Data = base64.split(',')[1] || base64;
  // Base64 is ~4/3 the size of binary
  return Math.round((base64Data.length * 3) / 4 / 1024);
}
