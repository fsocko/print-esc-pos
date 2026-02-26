// =======================
// GLOBAL STATE
// =======================
let contentFileName = 'segment';   // fallback name
let contentTitle = '';             // extracted <title> if present

// =======================
// LOAD CONTENT HTML
// =======================
function loadContentFile(input) {
    const file = input.files[0];
    if (!file) return;

    contentFileName = file.name.replace(/\.html$/i, '');
    contentTitle = '';

    const reader = new FileReader();
    reader.onload = e => {
        const html = e.target.result;

        // Extract <title> if present
        const match = html.match(/<title>(.*?)<\/title>/i);
        if (match && match[1]) {
            contentTitle = sanitizeName(match[1]);
        }

        document.getElementById('content').innerHTML = html;
        updateCutLines();
    };
    reader.readAsText(file);
}

// =======================
// LOAD HTML FROM TEXTAREA
// =======================
function loadFromTextarea() {
    const html = document.getElementById('html-input').value.trim();
    if (!html) return;

    contentFileName = 'pasted';
    contentTitle = '';

    // Extract <title> if present
    const match = html.match(/<title>(.*?)<\/title>/i);
    if (match && match[1]) {
        contentTitle = sanitizeName(match[1]);
    }

    document.getElementById('content').innerHTML = html;
    updateCutLines();
}

// =======================
// PRESET HANDLING
// =======================
function applyPreset() {
    const preset = document.getElementById('cutPreset').value;
    const mmInput = document.getElementById('cutLengthMm');

    if (preset) {
        mmInput.value = preset;
    }

    updateCutLines();
}

// =======================
// CUT LINE HANDLING
// =======================
function updateCutLines() {
    const content = document.getElementById('content');
    const mm = parseFloat(document.getElementById('cutLengthMm').value);
    const segmented = document.getElementById('splitToggle').checked;

    // Remove existing lines
    content.querySelectorAll('.generated-cut-line').forEach(el => el.remove());

    if (!mm || mm <= 0) return;

    const pxPerMm = 96 / 25.4;
    const intervalPx = mm * pxPerMm;
    const contentHeight = content.offsetHeight;

    for (let topPx = intervalPx; topPx < contentHeight; topPx += intervalPx) {
        const line = document.createElement('div');
        line.className = 'generated-cut-line';
        line.style.top = `${topPx}px`;

        // IMPORTANT:
        // segmentation ON → hide visually, but KEEP layout
        if (segmented) {
            line.style.visibility = 'hidden';
        }

        content.appendChild(line);
    }
}

// =======================
// EXPORT PNG / ZIP
// =======================
async function exportPNG() {
    const content = document.getElementById('content');
    const segmented = document.getElementById('splitToggle').checked;
    const cutLines = Array.from(content.querySelectorAll('.generated-cut-line'));

    // Resolve base name
    const baseName =
        contentTitle ||
        contentFileName ||
        'segment';

    // =======================
    // SINGLE IMAGE EXPORT
    // =======================
    if (!segmented) {
        const canvas = await html2canvas(content, { scale: 2 });
        downloadCanvas(canvas, `${baseName}.png`);
        return;
    }

    // =======================
    // SEGMENTED EXPORT
    // =======================
    const cutPositions = cutLines
        .map(el => el.offsetTop)
        .sort((a, b) => a - b);

    const segments = [0, ...cutPositions, content.offsetHeight];
    const zip = new JSZip();

    for (let i = 0; i < segments.length - 1; i++) {
        const yStart = segments[i];
        const yEnd = segments[i + 1];
        const height = yEnd - yStart;

        // Safety guard (should not trigger now)
        if (height <= 0) continue;

        const canvas = await html2canvas(content, {
            scale: 2,
            y: yStart,
            height
        });

        const index = String(i + 1).padStart(3, '0');
        const filename = `${index}_segment.png`;

        zip.file(
            filename,
            canvas.toDataURL('image/png').split(',')[1],
            { base64: true }
        );
    }

    const blob = await zip.generateAsync({ type: 'blob' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `${baseName}.zip`;
    link.click();
}

// =======================
// HELPERS
// =======================
function downloadCanvas(canvas, filename) {
    const link = document.createElement('a');
    link.download = filename;
    link.href = canvas.toDataURL('image/png');
    link.click();
}

function sanitizeName(name) {
    return name
        .trim()
        .replace(/\s+/g, '_')
        .replace(/[^\w\-]+/g, '');
}
