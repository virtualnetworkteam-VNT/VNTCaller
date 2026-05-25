package com.vnt.caller;
import android.content.Context;
import android.media.AudioFormat;
import android.media.AudioManager;
import android.media.AudioRecord;
import android.media.AudioTrack;
import android.media.MediaRecorder;
import android.telecom.Connection;
import android.telecom.DisconnectCause;
import android.util.Log;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.Socket;

public class VNTConnection extends Connection {
    private static final String TAG = "VNTConn";
    private static final String BRIDGE_HOST = "192.168.10.96";
    private static final int BRIDGE_PORT = 9999;
    private static final int SAMPLE_RATE = 16000;
    private final Context ctx;
    private Socket socket;
    private AudioRecord recorder;
    private AudioTrack player;
    private volatile boolean running = false;

    public VNTConnection(Context ctx) { this.ctx = ctx; }

    public void startAIBridge(String caller) {
        Log.i(TAG, "Starting AI bridge for: " + caller);
        AudioManager am = (AudioManager) ctx.getSystemService(Context.AUDIO_SERVICE);
        am.setMode(AudioManager.MODE_IN_COMMUNICATION);
        running = true;
        new Thread(() -> {
            try {
                socket = new Socket(BRIDGE_HOST, BRIDGE_PORT);
                OutputStream out = socket.getOutputStream();
                InputStream in = socket.getInputStream();
                // Send caller ID
                out.write((caller + "\n").getBytes());


                out.flush();

                int bufSize = AudioRecord.getMinBufferSize(SAMPLE_RATE,
                    AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT) * 2;

                // Try VOICE_CALL source first (captures both sides of call)
                // Falls back to VOICE_COMMUNICATION if not available
                int audioSource = MediaRecorder.AudioSource.VOICE_CALL;
                recorder = new AudioRecord(audioSource, SAMPLE_RATE,
                    AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT, bufSize);
                if (recorder.getState() != AudioRecord.STATE_INITIALIZED) {
                    recorder.release();
                    recorder = new AudioRecord(MediaRecorder.AudioSource.VOICE_COMMUNICATION,
                        SAMPLE_RATE, AudioFormat.CHANNEL_IN_MONO,
                        AudioFormat.ENCODING_PCM_16BIT, bufSize);
                }

                int playBuf = AudioTrack.getMinBufferSize(SAMPLE_RATE,
                    AudioFormat.CHANNEL_OUT_MONO, AudioFormat.ENCODING_PCM_16BIT) * 2;
                player = new AudioTrack(AudioManager.STREAM_VOICE_CALL, SAMPLE_RATE,
                    AudioFormat.CHANNEL_OUT_MONO, AudioFormat.ENCODING_PCM_16BIT,
                    playBuf, AudioTrack.MODE_STREAM);

                recorder.startRecording();
                player.play();

                // Read AI response audio
                new Thread(() -> {
                    byte[] buf = new byte[4096];
                    try {
                        int r;
                        while (running && (r = in.read(buf)) > 0) {
                            player.write(buf, 0, r);
                        }
                    } catch (Exception ignored) {}
                }).start();

                // Send mic/call audio to AI
                byte[] buf = new byte[bufSize];
                while (running) {
                    int r = recorder.read(buf, 0, buf.length);
                    if (r > 0) { out.write(buf, 0, r); out.flush(); }
                }
            } catch (Exception e) {
                Log.e(TAG, "Bridge error: " + e.getMessage());
            }
        }).start();
    }

    private void cleanup() {
        running = false;
        try { if (recorder != null) { recorder.stop(); recorder.release(); } } catch (Exception ignored) {}
        try { if (player != null) { player.stop(); player.release(); } } catch (Exception ignored) {}
        try { if (socket != null) socket.close(); } catch (Exception ignored) {}
        try {
            AudioManager am = (AudioManager) ctx.getSystemService(Context.AUDIO_SERVICE);
            am.setMode(AudioManager.MODE_NORMAL);
        } catch (Exception ignored) {}
    }

    @Override public void onDisconnect() {
        cleanup();
        setDisconnected(new DisconnectCause(DisconnectCause.LOCAL));
        destroy();
    }
    @Override public void onAbort() { cleanup(); setDisconnected(new DisconnectCause(DisconnectCause.UNKNOWN)); destroy(); }
}
