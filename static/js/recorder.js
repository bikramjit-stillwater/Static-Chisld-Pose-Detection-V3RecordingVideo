/**
 * In-browser video recording using MediaRecorder API.
 * No third-party API key needed - all native to the browser.
 *
 * Exposes: window.PoseRecorder with start/stop/getBlob/reset methods.
 */
(function () {
    'use strict';

    let mediaStream = null;       // active camera stream
    let mediaRecorder = null;     // MediaRecorder instance
    let recordedChunks = [];      // raw chunks while recording
    let recordedBlob = null;      // final assembled blob (after stop)
    let recordingMimeType = '';   // e.g. video/webm
    let timerInterval = null;
    let startTime = 0;

    const previewEl = () => document.getElementById('record-preview');
    const timerEl = () => document.getElementById('record-timer');
    const btnCamera = () => document.getElementById('btn-start-camera');
    const btnStart = () => document.getElementById('btn-start-record');
    const btnStop = () => document.getElementById('btn-stop-record');
    const btnDiscard = () => document.getElementById('btn-discard');

    function pickSupportedMimeType() {
        // MediaRecorder format support varies by browser. Try in preferred order.
        const types = [
            'video/webm;codecs=vp9,opus',
            'video/webm;codecs=vp8,opus',
            'video/webm;codecs=vp9',
            'video/webm;codecs=vp8',
            'video/webm',
            'video/mp4',
        ];
        for (const t of types) {
            if (window.MediaRecorder && MediaRecorder.isTypeSupported(t)) {
                return t;
            }
        }
        return ''; // browser will use its default
    }

    function formatTime(ms) {
        const totalSec = Math.floor(ms / 1000);
        const m = String(Math.floor(totalSec / 60)).padStart(2, '0');
        const s = String(totalSec % 60).padStart(2, '0');
        return `${m}:${s}`;
    }

    function updateTimer() {
        const el = timerEl();
        if (el) el.textContent = formatTime(Date.now() - startTime);
    }

    async function startCamera() {
        try {
            // Request user-facing camera by default; on mobile, environment cam.
            const constraints = {
                video: {
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    facingMode: 'user',
                },
                audio: false,
            };
            mediaStream = await navigator.mediaDevices.getUserMedia(constraints);
            const v = previewEl();
            v.srcObject = mediaStream;
            v.muted = true;
            v.play();

            btnCamera().disabled = true;
            btnStart().disabled = false;
            btnStop().disabled = true;
            btnDiscard().style.display = 'none';
        } catch (err) {
            console.error('Camera error:', err);
            alert(
                'Could not access camera.\n\n' +
                'Please make sure:\n' +
                '• You granted camera permission\n' +
                '• You are using HTTPS (or localhost)\n' +
                '• No other app is using the camera\n\n' +
                'Error: ' + err.message
            );
        }
    }

    function startRecording() {
        if (!mediaStream) {
            alert('Please start the camera first.');
            return;
        }
        recordedChunks = [];
        recordedBlob = null;

        recordingMimeType = pickSupportedMimeType();
        const options = recordingMimeType ? { mimeType: recordingMimeType } : {};

        try {
            mediaRecorder = new MediaRecorder(mediaStream, options);
        } catch (err) {
            console.error('MediaRecorder error:', err);
            alert('Could not start recording: ' + err.message);
            return;
        }

        mediaRecorder.ondataavailable = (e) => {
            if (e.data && e.data.size > 0) {
                recordedChunks.push(e.data);
            }
        };

        mediaRecorder.onstop = () => {
            const type = recordingMimeType || 'video/webm';
            recordedBlob = new Blob(recordedChunks, { type });

            // Replace live stream with playback of the recording
            const v = previewEl();
            v.srcObject = null;
            v.src = URL.createObjectURL(recordedBlob);
            v.muted = true;
            v.controls = true;

            btnDiscard().style.display = '';

            // Stop the camera so the LED turns off
            if (mediaStream) {
                mediaStream.getTracks().forEach((t) => t.stop());
                mediaStream = null;
            }

            // Notify main.js that a recording is ready
            document.dispatchEvent(new CustomEvent('recording-ready', {
                detail: { blob: recordedBlob, mimeType: type },
            }));
        };

        mediaRecorder.start(250); // collect chunks every 250 ms

        startTime = Date.now();
        timerEl().classList.add('active');
        timerInterval = setInterval(updateTimer, 200);

        btnStart().disabled = true;
        btnStop().disabled = false;
        btnCamera().disabled = true;
    }

    function stopRecording() {
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
        }
        if (timerInterval) {
            clearInterval(timerInterval);
            timerInterval = null;
        }
        timerEl().classList.remove('active');
        btnStop().disabled = true;
        // btnStart will be re-enabled only via reset (discard) flow
    }

    function reset() {
        // Discard current recording and free resources
        recordedChunks = [];
        recordedBlob = null;

        if (mediaStream) {
            mediaStream.getTracks().forEach((t) => t.stop());
            mediaStream = null;
        }
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            try { mediaRecorder.stop(); } catch (e) { /* ignore */ }
        }
        mediaRecorder = null;

        const v = previewEl();
        if (v) {
            v.srcObject = null;
            v.removeAttribute('src');
            v.controls = false;
            v.load();
        }
        if (timerInterval) {
            clearInterval(timerInterval);
            timerInterval = null;
        }
        if (timerEl()) {
            timerEl().classList.remove('active');
            timerEl().textContent = '00:00';
        }

        btnCamera().disabled = false;
        btnStart().disabled = true;
        btnStop().disabled = true;
        btnDiscard().style.display = 'none';

        document.dispatchEvent(new CustomEvent('recording-cleared'));
    }

    function getBlob() {
        return recordedBlob;
    }

    function getMimeType() {
        return recordingMimeType || 'video/webm';
    }

    // Public API
    window.PoseRecorder = {
        startCamera,
        startRecording,
        stopRecording,
        reset,
        getBlob,
        getMimeType,
    };
})();
