package com.vnt.caller;
import android.content.Context;
import android.media.*;
import android.telecom.*;
import android.util.Log;
import org.java_websocket.client.WebSocketClient;
import org.java_websocket.handshake.ServerHandshake;
import java.net.URI;
import java.nio.ByteBuffer;

public class VNTConnection extends Connection {
    private static final String TAG = "VNTConnection";
    private static final String WS_HOST = "192.168.10.96";
    private static final int WS_PORT = 9999;
    private Context ctx;
    private WebSocketClient wsClient;
    private AudioRecord recorder;
    private AudioTrack player;
    private boolean running = false;
    private String callerNumber = "unknown";

    public VNTConnection(Context ctx) {
        this.ctx = ctx;
        setConnectionCapabilities(
            CAPABILITY_HOLD | CAPABILITY_SUPPORT_HOLD |
            CAPABILITY_MUTE | CAPABILITY_CAN_UPGRADE_TO_VIDEO
        );
    }

    public void startAIBridge(String caller) {
        this.callerNumber = caller != null ? caller.replaceAll("[^0-9]","") : "unknown";
        String clean = callerNumber.replaceAll("[^0-9]","");
        String room = clean.endsWith("568116899") ? "ryan-alias" : "vnt-general";
        String url = "ws://" + WS_HOST + ":" + WS_PORT + "/" + room + "?caller=" + callerNumber;
        Log.i(TAG, "Connecting to AI: " + url);

        new Thread(() -> {
            try {
                wsClient = new WebSocketClient(new URI(url)) {
                    @Override public void onOpen(ServerHandshake h) {
                        Log.i(TAG, "AI connected");
                        startAudio();
                    }
                    @Override public void onMessage(ByteBuffer buf) {
                        playAudio(buf.array());
                    }
                    @Override public void onMessage(String msg) {}
                    @Override public void onClose(int c, String r, boolean remote) {
                        stopAudio();
                        if (remote) disconnect();
                    }
                    @Override public void onError(Exception e) {
                        Log.e(TAG, "WS error: " + e.getMessage());
                    }
                };
                wsClient.connect();
            } catch (Exception e) {
                Log.e(TAG, "Bridge error: " + e.getMessage());
            }
        }).start();
    }

    private void startAudio() {
        int bufSize = AudioRecord.getMinBufferSize(16000,
            AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT);
        
        // Use VOICE_COMMUNICATION source for phone call audio
        recorder = new AudioRecord(
            MediaRecorder.AudioSource.VOICE_COMMUNICATION,
            16000, AudioFormat.CHANNEL_IN_MONO,
            AudioFormat.ENCODING_PCM_16BIT, bufSize * 4);
        
        // Output to earpiece
        player = new AudioTrack.Builder()
            .setAudioAttributes(new AudioAttributes.Builder()
                .setUsage(AudioAttributes.USAGE_VOICE_COMMUNICATION)
                .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH).build())
            .setAudioFormat(new AudioFormat.Builder()
                .setSampleRate(48000).setChannelMask(AudioFormat.CHANNEL_OUT_MONO)
                .setEncoding(AudioFormat.ENCODING_PCM_16BIT).build())
            .setBufferSizeInBytes(bufSize * 4)
            .setTransferMode(AudioTrack.MODE_STREAM).build();
        
        player.play();
        recorder.startRecording();
        running = true;
        
        // Stream mic audio to AI
        new Thread(() -> {
            byte[] buf = new byte[bufSize];
            while (running) {
                int read = recorder.read(buf, 0, buf.length);
                if (read > 0 && wsClient != null && wsClient.isOpen()) {
                    wsClient.send(ByteBuffer.wrap(buf, 0, read));
                }
            }
        }).start();
    }

    private void playAudio(byte[] data) {
        if (player != null && running) player.write(data, 0, data.length);
    }

    private void stopAudio() {
        running = false;
        if (recorder != null) { try { recorder.stop(); recorder.release(); } catch(Exception e){} }
        if (player != null) { try { player.stop(); player.release(); } catch(Exception e){} }
    }

    @Override
    public void onDisconnect() {
        stopAudio();
        if (wsClient != null) wsClient.close();
        setDisconnected(new DisconnectCause(DisconnectCause.LOCAL));
        destroy();
    }

    @Override
    public void onAbort() { onDisconnect(); }

    @Override
    public void onHold() { setOnHold(); }

    @Override
    public void onUnhold() { setActive(); }
}
