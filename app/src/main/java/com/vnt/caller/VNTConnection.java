package com.vnt.phone;

import android.content.Context;
import android.media.AudioFormat;
import android.media.AudioManager;
import android.media.AudioRecord;
import android.media.AudioTrack;
import android.media.MediaRecorder;
import android.telecom.Connection;
import android.telecom.DisconnectCause;
import android.util.Log;
import org.java_websocket.client.WebSocketClient;
import org.java_websocket.handshake.ServerHandshake;
import java.net.URI;
import java.nio.ByteBuffer;

public class VNTConnection extends Connection {
    private static final String TAG = "VNTConn";
    private static final String BRIDGE_URL = "ws://192.168.10.96:9999";
    private static final int SAMPLE_RATE = 16000;
    private final Context ctx;
    private WebSocketClient wsClient;
    private AudioRecord recorder;
    private AudioTrack player;
    private Thread recThread, playThread;
    private volatile boolean running = false;

    public VNTConnection(Context ctx) { this.ctx = ctx; }

    public void startAIBridge(String caller) {
        Log.i(TAG, "Starting AI bridge for: " + caller);
        try {
            // Set proper audio mode
            AudioManager am = (AudioManager) ctx.getSystemService(Context.AUDIO_SERVICE);
            am.setMode(AudioManager.MODE_IN_COMMUNICATION);
            am.setSpeakerphoneOn(false);

            URI uri = new URI(BRIDGE_URL + "?caller=" + caller);
            wsClient = new WebSocketClient(uri) {
                @Override public void onOpen(ServerHandshake h) {
                    Log.i(TAG, "Bridge connected");
                    startMic();
                }
                @Override public void onMessage(ByteBuffer bytes) {
                    // Received TTS audio from AI — play it
                    playAudio(bytes.array());
                }
                @Override public void onMessage(String msg) {
                    Log.i(TAG, "Bridge msg: " + msg);
                }
                @Override public void onClose(int c, String r, boolean remote) {
                    Log.i(TAG, "Bridge closed"); stopAudio();
                }
                @Override public void onError(Exception e) {
                    Log.e(TAG, "Bridge error: " + e.getMessage());
                }
            };
            wsClient.connect();
        } catch (Exception e) {
            Log.e(TAG, "Bridge start error: " + e.getMessage());
        }
    }

    private void startMic() {
        running = true;
        int bufSize = AudioRecord.getMinBufferSize(SAMPLE_RATE,
            AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT) * 4;
        recorder = new AudioRecord(MediaRecorder.AudioSource.VOICE_COMMUNICATION,
            SAMPLE_RATE, AudioFormat.CHANNEL_IN_MONO,
            AudioFormat.ENCODING_PCM_16BIT, bufSize);

        int playBuf = AudioTrack.getMinBufferSize(SAMPLE_RATE,
            AudioFormat.CHANNEL_OUT_MONO, AudioFormat.ENCODING_PCM_16BIT) * 4;
        player = new AudioTrack(AudioManager.STREAM_VOICE_CALL, SAMPLE_RATE,
            AudioFormat.CHANNEL_OUT_MONO, AudioFormat.ENCODING_PCM_16BIT,
            playBuf, AudioTrack.MODE_STREAM);

        recorder.startRecording();
        player.play();

        recThread = new Thread(() -> {
            byte[] buf = new byte[bufSize];
            while (running) {
                int read = recorder.read(buf, 0, buf.length);
                if (read > 0 && wsClient != null && wsClient.isOpen()) {
                    wsClient.send(ByteBuffer.wrap(buf, 0, read));
                }
            }
        });
        recThread.start();
    }

    private void playAudio(byte[] data) {
        if (player != null && running) player.write(data, 0, data.length);
    }

    private void stopAudio() {
        running = false;
        try { if (recorder != null) { recorder.stop(); recorder.release(); } } catch (Exception ignored) {}
        try { if (player != null) { player.stop(); player.release(); } } catch (Exception ignored) {}
        try { if (wsClient != null) wsClient.close(); } catch (Exception ignored) {}
        AudioManager am = (AudioManager) ctx.getSystemService(Context.AUDIO_SERVICE);
        am.setMode(AudioManager.MODE_NORMAL);
    }

    @Override public void onDisconnect() {
        stopAudio();
        setDisconnected(new DisconnectCause(DisconnectCause.LOCAL));
        destroy();
    }

    @Override public void onAbort() {
        stopAudio();
        setDisconnected(new DisconnectCause(DisconnectCause.UNKNOWN));
        destroy();
    }
}
