// Make sure to include JSZip in your HTML before script.js
// <script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.0/jszip.min.js"></script>

function loadContentFile(input) {
    const file = input.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = e => {
        document.getElementById('content').innerHTML = e.target.result;
        updateCutLines();
    };
    reader.readAsText(file);
}

/* PRESET HANDLING */
function applyPreset() {
    const preset = document.getElementById('cutPreset').value;
    const mmInput = document.getElementById('cutLengthMm');

    if (preset) {
        mmInput.value = preset;
    }

    updateCutLines();
}

/* MULTIPLE CUT LINES WITH LABELS */
function updateCutLines() {
    const content = document.getElementById('content');
    const mm = parseFloat(document.getElementById('cutLengthMm').value);

    content.querySelectorAll('.generated-cut-line').forEach(el => el.remove());

    if (!mm || mm <= 0) return;

    const pxPerMm = 96 / 25.4;
    const intervalPx = mm * pxPerMm;
    const contentHeight = content.offsetHeight;

    for (let topPx = intervalPx; topPx < contentHeight; topPx += intervalPx) {
        const line = document.createElement('div');
        line.className = 'generated-cut-line';
        line.style.top = `${topPx}px`;
        content.appendChild(line);
    }
}

/* EXPORT TO PNG OR ZIP */
async function exportPNG() {
    const content = document.getElementById('content');
    const segmented = document.getElementById('splitToggle').checked;
    const pageTitle = document.title.replace(/\s+/g, '_') || 'page';

    if (!segmented) {
        const canvas = await html2canvas(content, { scale: 2 });
        downloadCanvas(canvas, `${pageTitle}.png`);
        return;
    }

    // Get cut line positions
    const cutLines = Array.from(content.querySelectorAll('.generated-cut-line'))
                          .map(el => el.offsetTop)
                          .sort((a,b) => a-b);

    const segments = [0, ...cutLines, content.offsetHeight];

    const zip = new JSZip();

    for (let i = 0; i < segments.length - 1; i++) {
        const yStart = segments[i];
        const yEnd = segments[i + 1];
        const segmentHeight = yEnd - yStart;

        const canvas = await html2canvas(content, {
            scale: 2,
            height: segmentHeight,
            y: yStart,
        });

        const dataUrl = canvas.toDataURL('image/png');
        const base64 = dataUrl.split(',')[1];
        zip.file(`segment_${i + 1}.png`, base64, {base64: true});
    }

    zip.generateAsync({type: "blob"}).then(function(contentBlob) {
        const link = document.createElement('a');
        link.href = URL.createObjectURL(contentBlob);
        link.download = `${pageTitle}.zip`;
        link.click();
    });
}

function downloadCanvas(canvas, filename) {
    const link = document.createElement('a');
    link.download = filename;
    link.href = canvas.toDataURL('image/png');
    link.click();
}
