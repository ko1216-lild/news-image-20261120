// main.ts -- validated publisher for the news-image-20261120 entry.
//
// The poster itself is produced ahead of time by build_image.py and
// committed next to this file as entry.png.  This program is the
// entrypoint the make.fun program/v1 harness runs: it must place one
// valid image at <output>/entry.png and fail loudly when the committed
// image does not meet the competition limits.
//
// What it does, in order:
//   1. Resolves the output directory from MAKEFUN_OUTPUT_DIR
//      (default "/output", the harness mount point).
//   2. Reads entry.png from this file's own directory.
//   3. Validates the bytes: PNG signature, IHDR chunk, width and
//      height each between 1 and 1024, and a total size of at most
//      1 MiB (1048576 bytes).
//   4. Copies the validated bytes unchanged to <output>/entry.png.
//      Copying unchanged is deliberate: the poster is deterministic,
//      so re-encoding here could only risk changing its bytes.
//
// Exit code 0 means the output file was written.  Any validation
// problem prints one clear line to stderr and exits with code 1
// before anything is copied.

import { copyFileSync, mkdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

// Competition limits for the delivered image.
const MAX_BYTES = 1_048_576; // 1 MiB
const MAX_SIDE = 1024; // width and height may not exceed this

// The eight-byte PNG file signature every PNG must start with.
const PNG_SIGNATURE: readonly number[] = [
  0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a,
];

function fail(message: string): never {
  console.error(`news-image-20261120: error: ${message}`);
  process.exit(1);
}

function readUint32BE(buf: Buffer, offset: number): number {
  // Manual big-endian read so the intent stays obvious; Buffer's own
  // readUInt32BE would do the same job.
  return (
    buf[offset] * 0x1000000 +
    ((buf[offset + 1] << 16) | (buf[offset + 2] << 8) | buf[offset + 3])
  );
}

interface PngInfo {
  width: number;
  height: number;
  bytes: number;
}

function validatePng(buf: Buffer, sourcePath: string): PngInfo {
  if (buf.length === 0) {
    fail(`entry image is empty: ${sourcePath}`);
  }
  if (buf.length > MAX_BYTES) {
    fail(
      `entry image is ${buf.length} bytes, over the ${MAX_BYTES}-byte limit`,
    );
  }
  if (buf.length < PNG_SIGNATURE.length + 24) {
    fail("entry image is too short to be a PNG with an IHDR chunk");
  }
  for (let i = 0; i < PNG_SIGNATURE.length; i += 1) {
    if (buf[i] !== PNG_SIGNATURE[i]) {
      fail("entry image does not start with the PNG signature");
    }
  }
  // The first chunk after the signature must be IHDR: bytes 8..11 hold
  // its length (13 for IHDR) and bytes 12..15 hold the ASCII type.
  const ihdrType = buf.toString("ascii", 12, 16);
  if (ihdrType !== "IHDR") {
    fail(`first PNG chunk is "${ihdrType}", expected "IHDR"`);
  }
  const width = readUint32BE(buf, 16);
  const height = readUint32BE(buf, 20);
  if (width < 1 || height < 1) {
    fail(`PNG dimensions ${width}x${height} are not positive`);
  }
  if (width > MAX_SIDE || height > MAX_SIDE) {
    fail(
      `PNG dimensions ${width}x${height} exceed the ${MAX_SIDE}x${MAX_SIDE} limit`,
    );
  }
  return { width, height, bytes: buf.length };
}

function main(): void {
  const here = dirname(fileURLToPath(import.meta.url));
  const sourcePath = join(here, "entry.png");

  let info: PngInfo;
  let raw: Buffer;
  try {
    const st = statSync(sourcePath);
    if (!st.isFile()) {
      fail(`entry image is not a regular file: ${sourcePath}`);
    }
    raw = readFileSync(sourcePath);
  } catch (err) {
    if ((err as NodeJS.ErrnoException).code === "ENOENT") {
      fail(`entry image not found next to main.ts: ${sourcePath}`);
    }
    throw err;
  }

  info = validatePng(raw, sourcePath);

  const outputDir = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";
  const outputPath = join(outputDir, "entry.png");
  mkdirSync(outputDir, { recursive: true });

  // Guard against an output directory that resolves to the source
  // file's own directory: there the output path would be the source
  // path itself, and copying a file onto itself is never intended.
  // Comparing device and inode of the two directories follows
  // symlinks and relative spellings such as "." for free.
  const outDirStat = statSync(outputDir);
  const sourceDirStat = statSync(here);
  if (outDirStat.dev === sourceDirStat.dev && outDirStat.ino === sourceDirStat.ino) {
    fail(
      `output directory resolves to the source directory, ` +
        `refusing to overwrite the source image: ${outputPath}`,
    );
  }

  copyFileSync(sourcePath, outputPath);

  // Read the written file back and verify it byte-for-byte against
  // the source we validated. A copy that silently truncated or
  // altered the poster would otherwise go unnoticed by the harness,
  // so any mismatch is a hard failure rather than a warning.
  let written: Buffer;
  try {
    written = readFileSync(outputPath);
  } catch (err) {
    fail(
      `could not read back the written output ${outputPath}: ` +
        `${(err as Error).message}`,
    );
  }
  if (!written.equals(raw)) {
    fail(
      `written output differs from the source image: ` +
        `${outputPath} has ${written.length} bytes, ` +
        `source has ${raw.length} bytes`,
    );
  }

  console.log(
    `news-image-20261120: wrote ${outputPath} ` +
      `(${info.bytes} bytes, ${info.width}x${info.height})`,
  );
  // Machine-readable summary of the successful publish, so a caller
  // can record exactly what was delivered without parsing the
  // human-readable line above.
  console.log(
    JSON.stringify({
      output: outputPath,
      bytes: info.bytes,
      width: info.width,
      height: info.height,
      verified: true,
    }),
  );
}

main();
