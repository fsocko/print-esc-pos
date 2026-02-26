// =======================
// GLOBAL STATE
// =======================
let contentFileName = 'segment';
let contentTitle = '';

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
// PRESET HANDLING
// =======================
function applyPreset() {
    const preset = document.getElementById('cutPreset').value;
    if (preset) {
        document.getElementById('cutLengthMm').value = preset;
    }
    updateCutLines();
}

// =======================
// CUT LINES
// =======================
function updateCutLines() {
    const content = document.getElementById('content');
    const mm = parseFloat(document.getElementById('cutLengthMm').value);
    const segmented = document.getElementById('splitToggle').checked;

    content.querySelectorAll('.generated-cut-line').forEach(el => el.remove());

    if (!mm || mm <= 0) {
        updateStackPreview();
        return;
    }

    const pxPerMm = 96 / 25.4;
    const intervalPx = mm * pxPerMm;
    const height = content.offsetHeight;

    for (let y = intervalPx; y < height; y += intervalPx) {
        const line = document.createElement('div');
        line.className = 'generated-cut-line';
        line.style.top = `${y}px`;
        if (segmented) line.style.visibility = 'hidden';
        content.appendChild(line);
    }

    updateStackPreview();
}

// =======================
// STACKED PREVIEW
// =======================
async function updateStackPreview() {
    const content = document.getElementById('content');
    const preview = document.getElementById('stackPreview');

    preview.innerHTML = '';

    const cutLines = Array.from(
        content.querySelectorAll('.generated-cut-line')
    );

    const cutPositions = cutLines
        .map(el => el.offsetTop)
        .sort((a, b) => a - b);

    const segments = [0, ...cutPositions, content.offsetHeight];

    for (let i = 0; i < segments.length - 1; i++) {
        const yStart = segments[i];
        const yEnd = segments[i + 1];
        const height = yEnd - yStart;
        if (height <= 0) continue;

        const canvas = await html2canvas(content, {
            scale: 1,
            y: yStart,
            height,
            backgroundColor: '#fff'
        });

        const img = document.createElement('img');
        img.src = canvas.toDataURL('image/png');
        img.className = 'stack-strip';

        preview.appendChild(img);
    }
}

// =======================
// EXPORT (SEGMENTED ONLY)
// =======================
async function exportPNG() {
    const content = document.getElementById('content');

    const cutLines = Array.from(
        content.querySelectorAll('.generated-cut-line')
    );

    const cutPositions = cutLines
        .map(el => el.offsetTop)
        .sort((a, b) => a - b);

    const segments = [0, ...cutPositions, content.offsetHeight];
    const zip = new JSZip();

    const baseName = contentTitle || contentFileName || 'segment';

    for (let i = 0; i < segments.length - 1; i++) {
        const yStart = segments[i];
        const yEnd = segments[i + 1];
        const height = yEnd - yStart;
        if (height <= 0) continue;

        const canvas = await html2canvas(content, {
            scale: 2,
            y: yStart,
            height,
            backgroundColor: '#fff'
        });

        const index = String(i + 1).padStart(3, '0');
        zip.file(
            `${index}_strip.png`,
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
function sanitizeName(name) {
    return name
        .trim()
        .replace(/\s+/g, '_')
        .replace(/[^\w\-]+/g, '');
}
